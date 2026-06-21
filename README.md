# 🛡️ Multi-Agent RAG Compliance Auditor

> Automated compliance auditing powered by RAG, vector search, and a 3-agent AI pipeline — built with CrewAI, Gemini, and Streamlit.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-4B8BBE)](https://www.crewai.com/)
[![Gemini](https://img.shields.io/badge/LLM-Gemini%201.5%20Pro-4285F4?logo=google)](https://ai.google.dev/)
[![Qdrant](https://img.shields.io/badge/Vector%20DB-Qdrant-red)](https://qdrant.tech/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Problem Statement

Companies spend thousands of hours manually checking internal policies, codebases, and documents against complex, ever-evolving regulations. A single compliance review of a 200-page document can take weeks and cost tens of thousands of dollars.

This project automates that process end-to-end — upload a document, and three specialized AI agents return a structured compliance report with a score, flagged violations, legal risk assessments, and actionable fix recommendations.

---

## 🎬 Demo

> Upload any PDF policy document → get a compliance score in minutes.

```
User uploads PDF
      ↓
Ingestion pipeline (parse → chunk → embed → store in Qdrant)
      ↓
Agent 1: Compliance Checker  →  flags violations via RAG retrieval
      ↓
Agent 2: Legal Auditor       →  confirms findings, assesses legal risk
      ↓
Agent 3: Report Compiler     →  produces structured JSON report + score
      ↓
Streamlit UI displays score card, violation table, recommendations
```

---

## ✨ Features

- **PDF ingestion pipeline** — parses dense, unstructured PDFs page by page, chunks them intelligently, and stores semantic embeddings in Qdrant
- **RAG-powered retrieval** — each agent retrieves only the most relevant regulatory rules for a given passage (not the full document)
- **3-agent CrewAI pipeline** running sequentially, each building on the last agent's output
- **Structured JSON report** with compliance score (0–100), violations ranked by severity, and prioritized recommendations
- **Interactive Streamlit UI** with color-coded score card, filterable violations table, and one-click JSON download
- **Built-in mock regulatory rules** (REG-101 through REG-105) for immediate testing without real documents
- **Graceful fallback** — runs with in-memory Qdrant if no cloud credentials are provided

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    STREAMLIT UI (app.py)                 │
│   File uploader │ Score card │ Violations │ Download     │
└────────────────────────┬────────────────────────────────┘
                         │ PDF upload
┌────────────────────────▼────────────────────────────────┐
│              INGESTION PIPELINE (pipeline/)              │
│  pdfplumber → LangChain Splitter → SentenceTransformers  │
│                     → Qdrant upsert                      │
└────────────────────────┬────────────────────────────────┘
                         │ chunks + embeddings stored
┌────────────────────────▼────────────────────────────────┐
│                VECTOR DATABASE (Qdrant)                  │
│         Semantic search over regulatory rules            │
└──────┬─────────────────┬────────────────────┬───────────┘
       │                 │                    │
┌──────▼──────┐  ┌───────▼──────┐  ┌─────────▼──────────┐
│   Agent 1   │  │   Agent 2    │  │      Agent 3        │
│  Compliance │→ │    Legal     │→ │  Report Compiler    │
│   Checker   │  │   Auditor    │  │                     │
│ Flags rules │  │ Confirms risk│  │ Score + JSON report │
└─────────────┘  └──────────────┘  └─────────────────────┘
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| PDF Parsing | pdfplumber |
| Text Chunking | LangChain `RecursiveCharacterTextSplitter` |
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2, local) |
| Vector DB | Qdrant (Cloud or in-memory fallback) |
| Multi-Agent Framework | crewai[google-genai] |
| LLM Backbone | Gemini 1.5 Pro (Google AI API) |
| Config & Secrets | python-dotenv / Streamlit secrets |

---

## 📁 Project Structure

```
Multi-Agent-RAG-Compliance-Auditor/
├── app.py                    # Streamlit UI entry point
├── config.py                 # All settings and env vars
├── crew.py                   # CrewAI crew + task orchestration
├── verify.py                 # Import verification script
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
├── .streamlit/
│   └── secrets.toml.example  # Template for Streamlit Cloud secrets
├── pipeline/
│   ├── __init__.py
│   ├── ingestion.py          # PDF → chunks → embeddings → Qdrant
│   └── retriever.py          # Semantic similarity search
└── agents/
    ├── __init__.py
    ├── compliance_checker.py  # Agent 1: flags violations
    ├── legal_auditor.py       # Agent 2: assesses legal risk
    └── report_compiler.py    # Agent 3: compiles final report
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- A [Google AI API key](https://aistudio.google.com/app/apikey) (free tier available)
- (Optional) A [Qdrant Cloud](https://cloud.qdrant.io/) account for persistent storage

### 1. Clone the repository

```bash
git clone https://github.com/Krishna-Dhawangale/Multi-Agent-RAG-Compliance-Auditor.git
cd Multi-Agent-RAG-Compliance-Auditor
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your keys:

```env
# Required
GOOGLE_API_KEY=your-google-ai-api-key-here

# Optional — leave blank to use in-memory Qdrant (no persistence)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
```

### 5. Verify your setup

```bash
python verify.py
```

### 6. Launch the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🧪 Testing the App

The app ships with **5 built-in mock regulatory rules** so you can test without any real regulatory documents.

1. Click **"📚 Load Mock Regulatory Rules"** in the sidebar — this populates Qdrant with sample rules
2. Upload any internal policy PDF (or use a sample document)
3. Click **"Run Compliance Audit"**
4. Review the score card, violations table, and download the JSON report

### Built-in Mock Rules

| Rule ID | Description |
|---|---|
| REG-101 | Password hashing requirements (bcrypt / Argon2) |
| REG-102 | Financial transaction authorization thresholds |
| REG-103 | MFA requirements for production server access |
| REG-104 | PII encryption standards (AES-256 / TLS 1.3) |
| REG-105 | Employee compliance training timelines |

---

## 🤖 Agent Breakdown

### Agent 1 — Compliance Checker
Scans the uploaded document section by section. For each passage, it queries Qdrant to retrieve the most relevant regulatory rules and flags any potential violations with the exact text and rule reference.

**Output:** List of `{violation_text, rule_violated, severity, page_number}`

### Agent 2 — Legal Auditor
Receives Agent 1's findings and applies legal reasoning to each flagged item. Confirms whether it is a genuine violation, assesses the legal risk level, and drafts corrective actions.

**Output:** List of `{confirmed, legal_risk, corrective_action, original_finding}`

### Agent 3 — Report Compiler
Aggregates both agents' outputs into a single structured compliance report. Calculates an overall score, writes an executive summary, and prioritizes the fix list.

**Output:** Structured JSON report (see below)

---

## 📊 Report Output Format

```json
{
  "score": 72,
  "summary": "The document contains 3 potential compliance violations across password storage, PII handling, and MFA enforcement.",
  "violations": [
    {
      "violation_text": "Passwords are stored in plaintext in our database.",
      "rule_violated": "REG-101: Passwords must be hashed using bcrypt or Argon2.",
      "severity": "high",
      "page_number": 3,
      "confirmed": true,
      "legal_risk": "High — exposes company to GDPR fines and data breach liability.",
      "corrective_action": "Immediately migrate to bcrypt password hashing with salt rounds ≥ 12."
    }
  ],
  "recommendations": [
    "Urgently update password storage to bcrypt.",
    "Implement AES-256 encryption for all PII fields at rest.",
    "Enforce MFA for all production server access within 30 days."
  ],
  "metadata": {
    "doc_name": "internal_policy_v2.pdf",
    "audit_date": "2026-06-22 10:30:00",
    "total_chunks": 47
  }
}
```

---

## ☁️ Deployment

### Streamlit Community Cloud (Recommended — Free)

1. Push this repository to GitHub (already done)
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Set **Main file path** to `app.py`
4. Under **Advanced settings → Secrets**, add:

```toml
GOOGLE_API_KEY = "your-google-ai-api-key-here"
QDRANT_URL = "https://your-cluster.qdrant.io"
QDRANT_API_KEY = "your-qdrant-api-key"
```

5. Click **Deploy** — your app goes live at `your-app-name.streamlit.app`

> **Note:** Streamlit Community Cloud has no persistent disk. Always use Qdrant Cloud (not in-memory mode) for deployed instances.

### Hugging Face Spaces (Alternative)

1. Create a new Space with **Streamlit** as the SDK
2. Push this repo as the Space source
3. Add secrets via the Space settings panel

---

## 🔧 Configuration Reference

All settings live in `config.py` and can be overridden via environment variables.

| Variable | Default | Description |
|---|---|---|
| `CHUNK_SIZE` | `500` | Token size per text chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between consecutive chunks |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local sentence-transformer model |
| `COLLECTION_NAME` | `compliance_docs` | Qdrant collection name |
| `TOP_K_RESULTS` | `5` | Number of chunks retrieved per query |

---

## 🛣️ Roadmap

- [ ] OCR support for scanned PDFs (Tesseract integration)
- [ ] Multi-document comparison (policy vs regulation side-by-side)
- [ ] Support for GDPR, HIPAA, SOC 2 as pre-loaded regulatory frameworks
- [ ] Export report as PDF
- [ ] User authentication for multi-tenant deployment
- [ ] REST API endpoint for programmatic access

---

## 🤝 Contributing

Contributions are welcome. Please open an issue first to discuss what you'd like to change, then submit a pull request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 👤 Author

**Krishna Dhawangale**

[![GitHub](https://img.shields.io/badge/GitHub-Krishna--Dhawangale-black?logo=github)](https://github.com/Krishna-Dhawangale)

---

> ⭐ If this project helped you, consider giving it a star on GitHub — it helps others find it!
