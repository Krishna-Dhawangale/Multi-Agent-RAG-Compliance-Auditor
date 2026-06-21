from crewai import Agent, LLM

def get_report_compiler_agent(llm: LLM) -> Agent:
    """Creates and returns the Report Compiler agent."""
    return Agent(
        role="Report Compiler",
        goal="Take both agents' outputs and produce a structured final compliance report with an overall score (0–100), executive summary, violation breakdown by severity, and prioritized fix list.",
        backstory=(
            "You are an expert compliance report compiler. Your job is to synthesize "
            "the findings of the compliance checker and legal auditor into a professional, "
            "structured compliance report in JSON format."
        ),
        tools=[],
        llm=llm,
        verbose=True
    )
