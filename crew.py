import pdfplumber
import os
import json
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Literal
from crewai import Crew, Process, Task, LLM
from agents.compliance_checker import get_compliance_checker_agent
from agents.legal_auditor import get_legal_auditor_agent
from agents.report_compiler import get_report_compiler_agent
import config

# ==========================================
# Pydantic Schemas for Structured Crew Outputs
# ==========================================

class Violation(BaseModel):
    violation_text: str = Field(description="The exact text passage from the document that is violating a rule")
    rule_violated: str = Field(description="The regulatory rule or policy requirement that was violated")
    severity: Literal["low", "medium", "high"] = Field(description="Severity of the violation")
    page_number: int = Field(description="The page number where the violation text was found")

class ComplianceCheckerOutput(BaseModel):
    violations: List[Violation] = Field(description="List of violations flagged by the checker")

class LegalAuditedFinding(BaseModel):
    confirmed: bool = Field(description="Whether this is a genuine legal compliance violation")
    legal_risk: str = Field(description="Assessment of the legal risk and implications")
    corrective_action: str = Field(description="Suggested corrective actions or remedies")
    original_finding: Violation = Field(description="The original violation details identified by the compliance checker")

class LegalAuditorOutput(BaseModel):
    audited_findings: List[LegalAuditedFinding] = Field(description="List of findings with legal audit analysis")

class FinalReportViolation(BaseModel):
    violation_text: str = Field(description="The exact text passage from the document")
    rule_violated: str = Field(description="The rule violated")
    severity: Literal["low", "medium", "high"] = Field(description="Severity classification")
    page_number: int = Field(description="Page number")
    confirmed: bool = Field(description="Whether confirmed as violation by legal auditor")
    legal_risk: str = Field(description="Legal risk level and implications")
    corrective_action: str = Field(description="Recommended corrective action")

class ReportMetadata(BaseModel):
    doc_name: str = Field(description="Name of the audited document")
    audit_date: str = Field(description="Date when audit was run")
    total_chunks: int = Field(description="Total number of chunks ingested")

class ComplianceReport(BaseModel):
    score: int = Field(description="Overall compliance score from 0 to 100")
    summary: str = Field(description="Executive summary of the compliance audit")
    violations: List[FinalReportViolation] = Field(description="List of violations with severity and legal assessments")
    recommendations: List[str] = Field(description="Prioritized list of recommended fixes and actions")
    metadata: ReportMetadata = Field(description="Metadata of the audit report")

# ==========================================
# Orchestration Function
# ==========================================

def run_audit(uploaded_file_path: str, total_chunks: int = 0, model: str = None, api_key: str = None, client = None, collection_name: str = None) -> dict:
    """Instantiate agents, configure tasks, execute sequential Crew audit, and return final report."""
    
    # 1. Read document text
    text_content = []
    with pdfplumber.open(uploaded_file_path) as pdf:
        for idx, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text_content.append(f"--- Page {idx + 1} ---\n{page_text}")
                
    doc_text = "\n\n".join(text_content)
    if not doc_text.strip():
        raise ValueError("This PDF appears to be scanned. OCR support coming soon.")
        
    doc_name = os.path.basename(uploaded_file_path)
    audit_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 2. Setup LLM
    gemini_api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please provide it in the sidebar or environment.")
        
    llm_model = model or config.LLM_MODEL
    llm = LLM(
        model=llm_model,
        api_key=gemini_api_key
    )

    # 3. Instantiate Agents
    checker_agent = get_compliance_checker_agent(llm, client=client, collection_name=collection_name)
    auditor_agent = get_legal_auditor_agent(llm)
    compiler_agent = get_report_compiler_agent(llm)
    
    # 4. Define Tasks
    checker_task = Task(
        description=(
            "Read the following uploaded document page-by-page. For each page, "
            "use the custom retriever tool to query the vector database and check if there are "
            "any regulatory rules or policy guidelines violated by the text. "
            "Flag any potential violations and record the exact text, rule, severity, and page number.\n\n"
            "Document content:\n{document_text}"
        ),
        expected_output="A structured list of compliance violations with exact text, rule, severity, and page number.",
        agent=checker_agent,
        output_pydantic=ComplianceCheckerOutput
    )
    
    auditor_task = Task(
        description=(
            "Review the compliance checker's list of flagged violations. "
            "Apply legal reasoning to confirm if each violation is a genuine compliance risk, "
            "assess the legal risk level/implications, and suggest specific corrective actions for each."
        ),
        expected_output="A structured list of confirmed violations with legal risk, corrective action, and original finding details.",
        agent=auditor_agent,
        context=[checker_task],
        output_pydantic=LegalAuditorOutput
    )
    
    compiler_task = Task(
        description=(
            "Review the audited compliance findings and combine them into a final compliance report. "
            "Calculate an overall compliance score (0-100) where 100 means zero violations, and scores drop "
            "based on the number and severity of confirmed violations. "
            "Provide a high-quality executive summary, a clean breakdown of violations, and a list of "
            "prioritized recommendations (remedial steps).\n\n"
            "Document Metadata:\n"
            "- Document Name: {doc_name}\n"
            "- Audit Date: {audit_date}\n"
            "- Total Chunks: {total_chunks}"
        ),
        expected_output="A final compliance audit report JSON object containing: score, summary, violations, recommendations, and metadata.",
        agent=compiler_agent,
        context=[checker_task, auditor_task],
        output_pydantic=ComplianceReport
    )
    
    # 5. Create Crew
    crew = Crew(
        agents=[checker_agent, auditor_agent, compiler_agent],
        tasks=[checker_task, auditor_task, compiler_task],
        process=Process.sequential,
        verbose=True
    )
    
    # 6. Kickoff
    result = crew.kickoff(inputs={
        "document_text": doc_text,
        "doc_name": doc_name,
        "audit_date": audit_date,
        "total_chunks": total_chunks
    })
    
    # Parse the result
    try:
        if hasattr(result, "pydantic") and result.pydantic:
            return result.pydantic.dict()
        elif hasattr(result, "json_dict") and result.json_dict:
            return result.json_dict
        else:
            return json.loads(result.raw)
    except Exception as e:
        print(f"Error parsing Crew output directly: {e}. Attempting raw string parse.")
        try:
            return json.loads(result.raw)
        except Exception:
            return {"error": "Failed to parse report into structured JSON", "raw_output": result.raw}
