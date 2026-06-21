# 🛡️ Multi-Agent RAG Compliance Auditor

A production-ready, end-to-end compliance auditing application built with **Streamlit**, **CrewAI**, and **Anthropic Claude**. Upload regulatory PDFs and internal policy documents, then let a pipeline of three AI agents analyze them, identify violations, assess legal risk, and produce a structured compliance report with a score.

---

## 🏗️ Architecture

```
PDF Upload
    │
    ▼
[Ingestion Pipeline]
  ├── pdfplumber   → extract text per page
  ├── LangChain    → RecursiveCharacterTextSplitter
  ├── SentenceTransformers → embed chunks (all-MiniLM-L6-v2)
  └── Qdrant       → store vectors (cloud or in-memory)
          │
          ▼
[Multi-Agent Crew (CrewAI + Claude claude-sonnet-4-6)]
  ├── Agent 1: Compliance Checker  → finds violations using RAG tool
  ├── Agent 2: Legal Auditor       → confirms + assesses legal risk
  └── Agent 3: Report Compiler     → produces structured JSON report
          │
          ▼
[Streamlit UI]
  ├── Score card (color-coded)
  ├── Executive summary
  ├── Violations table (severity-colored)
  ├── Recommendations list
  └── JSON download button
```

---

## ⚙️ Tech Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| PDF Parsing | pdfplumber |
| Text Chunking | LangChain RecursiveCharacterTextSplitter |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector DB | Qdrant (cloud or in-memory fallback) |
| Agents | CrewAI |
| LLM | Claude claude-sonnet-4-6 (Anthropic API) |

---

## 🚀 Quick Start (Local)

### 1. Set up environment

```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure API keys

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

```ini
# .env
ANTHROPIC_API_KEY=your-anthropic-api-key

# Optional: Qdrant Cloud (defaults to in-memory if omitted)
QDRANT_URL=
QDRANT_API_KEY=
```

### 3. Run the app

```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
compliance_auditor/
├── app.py                  # Streamlit UI
├── config.py               # Settings and env vars
├── crew.py                 # CrewAI agents + task orchestration
├── verify.py               # Import verification script
├── requirements.txt        
├── .env.example            
├── .streamlit/
│   └── secrets.toml.example
├── pipeline/
│   ├── ingestion.py        # PDF → chunks → embeddings → Qdrant
│   └── retriever.py        # Semantic similarity search
└── agents/
    ├── compliance_checker.py
    ├── legal_auditor.py
    └── report_compiler.py
```

---

## 🧪 Testing with Mock Rules

The app ships with 5 built-in mock regulatory rules you can load via the sidebar to test immediately:

- **REG-101**: Password storage requirements (bcrypt/Argon2)
- **REG-102**: Financial transaction authorization thresholds
- **REG-103**: MFA requirements for production server access
- **REG-104**: PII encryption requirements (AES-256 / TLS 1.3)
- **REG-105**: Employee compliance training timelines

Click **"📚 Load Mock Regulatory Rules"** in the sidebar before uploading your document.

---

## ☁️ Deploying to Streamlit Community Cloud

1. Push this directory to a GitHub repository.
2. Connect your repo on [share.streamlit.io](https://share.streamlit.io).
3. Set the main file to `compliance_auditor/app.py`.
4. Add secrets in the Streamlit Cloud dashboard:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   QDRANT_URL = "https://..."
   QDRANT_API_KEY = "..."
   ```

---

## 📊 Report Output Format

```json
{
  "score": 72,
  "summary": "The document contains 3 potential compliance violations...",
  "violations": [
    {
      "violation_text": "Passwords are stored in plaintext in our database.",
      "rule_violated": "REG-101: Passwords must be hashed with bcrypt or Argon2.",
      "severity": "high",
      "page_number": 3,
      "confirmed": true,
      "legal_risk": "High — exposes company to GDPR fines and data breach liability.",
      "corrective_action": "Immediately migrate to bcrypt password hashing."
    }
  ],
  "recommendations": [
    "Urgently update password storage to use bcrypt.",
    "Implement AES-256 encryption for all PII at rest."
  ],
  "metadata": {
    "doc_name": "internal_policy_v2.pdf",
    "audit_date": "2026-06-10 18:00:00",
    "total_chunks": 47
  }
}
```
