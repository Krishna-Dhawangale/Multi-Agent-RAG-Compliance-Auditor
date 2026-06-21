import sys
import os

# ---- GLOBAL SSL BYPASS FOR CORPORATE PROXIES ----
import httpx

_orig_t = httpx.HTTPTransport.__init__
def _patch_t(self, *a, **k):
    k['verify'] = False
    _orig_t(self, *a, **k)
httpx.HTTPTransport.__init__ = _patch_t

_orig_at = httpx.AsyncHTTPTransport.__init__
def _patch_at(self, *a, **k):
    k['verify'] = False
    _orig_at(self, *a, **k)
httpx.AsyncHTTPTransport.__init__ = _patch_at

_orig_c = httpx.Client.__init__
def _patch_c(self, *a, **k):
    k['verify'] = False
    _orig_c(self, *a, **k)
httpx.Client.__init__ = _patch_c

_orig_ac = httpx.AsyncClient.__init__
def _patch_ac(self, *a, **k):
    k['verify'] = False
    _orig_ac(self, *a, **k)
httpx.AsyncClient.__init__ = _patch_ac
# -------------------------------------------------

# Ensure the app can locate its modules when run as `streamlit run app.py`
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import json
import pandas as pd
from pipeline.ingestion import ingest_pdf, clear_db, get_embedding_model, get_qdrant_client, reset_qdrant_client
from pipeline.retriever import retrieve
from crew import run_audit

# Set up page config
st.set_page_config(
    page_title="Compliance Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session isolation variables
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())[:8]

session_collection_name = f"compliance_docs_{st.session_state.session_id}"


# Custom premium styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles */
    .reportview-container {
        font-family: 'Outfit', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
    }
    
    /* Status Badge styling */
    .badge {
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-high {
        background-color: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .badge-medium {
        background-color: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .badge-low {
        background-color: rgba(59, 130, 246, 0.15);
        color: #3B82F6;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🛡️ Multi-Agent RAG Compliance Auditor")
st.markdown("Automate regulatory compliance checks and risk assessments using a RAG pipeline and CrewAI agents.")

# Initialize environment variables from sidebar inputs
st.sidebar.header("🔑 Credentials & API Keys")

# Get defaults from env
env_gemini = os.getenv("GEMINI_API_KEY", "")
env_qdrant_url = os.getenv("QDRANT_URL", "")
env_qdrant_key = os.getenv("QDRANT_API_KEY", "")

# Sidebar fields
gemini_key = st.sidebar.text_input(
    "Google Gemini API Key", 
    value=env_gemini, 
    type="password",
    help="Required for Gemini LLM processing"
)
gemini_model = st.sidebar.selectbox(
    "Google Gemini Model",
    options=[
        "gemini/gemini-2.5-flash",
        "gemini/gemini-2.5-pro",
        "gemini/gemini-1.5-flash",
        "gemini/gemini-1.5-pro",
        "gemini/gemini-3.1-pro-preview"
    ],
    index=0,
    help="Select the Gemini model. Flash models are recommended for faster performance and higher free-tier limits."
)
qdrant_url = st.sidebar.text_input(
    "Qdrant Cloud URL (Optional)", 
    value=env_qdrant_url, 
    type="password",
    help="Leave empty for local in-memory DB"
)
qdrant_key = st.sidebar.text_input(
    "Qdrant API Key (Optional)", 
    value=env_qdrant_key, 
    type="password",
    help="Leave empty for local in-memory DB"
)

# Active credentials (from user input, falling back to default environment vars)
active_gemini_key = gemini_key or os.getenv("GEMINI_API_KEY", "")
active_qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "")
active_qdrant_key = qdrant_key or os.getenv("QDRANT_API_KEY", "")

# Connect to Qdrant (session-isolated)
from qdrant_client import QdrantClient

if "qdrant_client" not in st.session_state or st.session_state.get("db_credentials_changed", False):
    if active_qdrant_url:
        try:
            url = active_qdrant_url.strip()
            api_key = active_qdrant_key.strip() if active_qdrant_key else None
            st.session_state.qdrant_client = QdrantClient(url=url, api_key=api_key, timeout=10)
            st.session_state.qdrant_client.get_collections()  # verify connection
        except Exception as e:
            st.sidebar.error(f"Failed to connect to Qdrant Cloud: {e}. Using local in-memory DB fallback.")
            st.session_state.qdrant_client = QdrantClient(":memory:")
    else:
        st.session_state.qdrant_client = QdrantClient(":memory:")
    st.session_state.db_credentials_changed = False

client = st.session_state.qdrant_client

# Show DB mode status
if active_qdrant_url:
    st.sidebar.info("🌐 **DB Mode:** Qdrant Cloud")
else:
    st.sidebar.info("💾 **DB Mode:** In-Memory (local)")

# Reset DB connection button (useful when credentials change)
if st.sidebar.button("🔄 Reset DB Connection"):
    st.session_state.db_credentials_changed = True
    st.sidebar.success("Connection reset. New credentials will be used on next action.")

# Show session isolation ID
st.sidebar.markdown(f"👤 **Session ID:** `{st.session_state.session_id}`")


# Sidebar Actions
st.sidebar.header("⚙️ Database Operations")

def ingest_mock_rules(client, collection_name: str):
    """Injects sample regulatory compliance guidelines directly to Qdrant."""
    from qdrant_client.models import PointStruct, VectorParams, Distance
    import uuid
    
    try:
        client.get_collection(collection_name)
    except Exception:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        
    mock_rules = [
        "REG-101: All user passwords must be hashed using bcrypt or Argon2 before storage. Storing passwords in plaintext or using MD5/SHA1 is strictly prohibited.",
        "REG-102: Any outward financial transaction exceeding $10,000 USD must undergo multi-party authorization, requiring approval from a department manager and a financial controller.",
        "REG-103: Access to internal production servers must require multi-factor authentication (MFA). Single-factor password login is not permitted for administrative access.",
        "REG-104: Personally Identifiable Information (PII) of customers must be encrypted at rest using AES-256 and in transit using TLS 1.3. Plaintext storage is a severe violation.",
        "REG-105: All employees must complete compliance and security awareness training within 30 days of their onboarding date, with annual refreshers thereafter."
    ]
    
    model = get_embedding_model()
    points = []
    for idx, rule in enumerate(mock_rules):
        vector = model.encode(rule).tolist()
        point_id = str(uuid.uuid4())
        payload = {
            "text": rule,
            "source_file": "regulatory_reference_mock.pdf",
            "page_number": 1,
            "chunk_index": idx
        }
        points.append(PointStruct(id=point_id, vector=vector, payload=payload))
        
    client.upsert(collection_name=collection_name, wait=True, points=points)
    return len(mock_rules)

if st.sidebar.button("📚 Load Mock Regulatory Rules"):
    try:
        rules_loaded = ingest_mock_rules(client, session_collection_name)
        st.sidebar.success(f"Loaded {rules_loaded} mock regulatory rules successfully!")
    except Exception as e:
        st.sidebar.error(f"Error loading rules: {e}")

if st.sidebar.button("🗑️ Clear Vector Database"):
    clear_db(client, session_collection_name)
    st.sidebar.success("Vector Database cleared successfully!")

# Main view
uploaded_file = st.file_uploader("Upload PDF Document to Audit", type=["pdf"])

if uploaded_file is not None:
    # API key check
    if not active_gemini_key:
        st.error("⚠️ Gemini API Key is missing. Please enter your key in the sidebar configuration.")
    else:
        # Create temp folder and write the file
        import uuid
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = uploaded_file.name.replace(" ", "_").replace("/", "_")
        temp_path = os.path.join(temp_dir, f"{unique_id}_{safe_filename}")
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        try:
            # Step 1: Ingestion
            with st.spinner("🔍 Ingesting document (parsing, chunking, embedding, uploading)..."):
                chunk_count = ingest_pdf(temp_path, client, session_collection_name)
                st.success(f"Ingested {chunk_count} chunks into Qdrant vector database.")
                
            # Step 2: Audit Run
            with st.spinner("🤖 Running multi-agent compliance audit (orchestrating CrewAI)..."):
                report = run_audit(
                    temp_path, 
                    total_chunks=chunk_count, 
                    model=gemini_model, 
                    api_key=active_gemini_key, 
                    client=client, 
                    collection_name=session_collection_name
                )
                
            if "error" in report:
                st.error(f"Audit failed to produce a valid report. Error: {report.get('error')}")
                if "raw_output" in report:
                    st.text_area("Raw LLM Output", report["raw_output"], height=400)
            else:
                st.balloons()
                
                # Report Display Section
                st.markdown("## 📊 Audit Report")
                
                # Compliance Score Card
                score = report.get("score", 0)
                if score >= 80:
                    color = "#10B981"  # Emerald
                    bg_color = "rgba(16, 185, 129, 0.1)"
                    status_lbl = "Strong Compliance"
                elif score >= 50:
                    color = "#F59E0B"  # Amber
                    bg_color = "rgba(245, 158, 11, 0.1)"
                    status_lbl = "Needs Attention"
                else:
                    color = "#EF4444"  # Red
                    bg_color = "rgba(239, 68, 68, 0.1)"
                    status_lbl = "High Risk / Non-Compliant"
                    
                st.markdown(f"""
                <div style="
                    padding: 2rem;
                    border-radius: 12px;
                    border: 2px solid {color};
                    background-color: {bg_color};
                    text-align: center;
                    margin-bottom: 2rem;
                ">
                    <span style="font-size: 1.1rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.1em;">Audit Score</span>
                    <h1 style="font-size: 5rem; margin: 0.5rem 0; color: {color}; font-weight: 800;">{score}%</h1>
                    <span style="font-size: 1.2rem; font-weight: 700; color: {color};">{status_lbl}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Executive Summary Expander
                with st.expander("📝 Executive Summary", expanded=True):
                    st.write(report.get("summary", "No executive summary provided."))
                    
                # Violations Table
                st.markdown("### ⚠️ Flagged Violations")
                violations_data = report.get("violations", [])
                
                if not violations_data:
                    st.success("🎉 No compliance violations detected!")
                else:
                    df = pd.DataFrame(violations_data)
                    
                    # Formatting/arranging columns
                    df_display = df.reindex(columns=[
                        "page_number", "severity", "confirmed", 
                        "rule_violated", "violation_text", 
                        "legal_risk", "corrective_action"
                    ])
                    
                    # Format column names for display
                    df_display.columns = [
                        "Page", "Severity", "Confirmed", 
                        "Rule Violated", "Exact Violation Text", 
                        "Legal Risk Level & Impact", "Recommended Action"
                    ]
                    
                    # Style function for Pandas DataFrame
                    def style_df(row):
                        styles = [''] * len(row)
                        sev = str(row["Severity"]).lower()
                        conf = row["Confirmed"]
                        
                        # Apply severity background styling
                        if conf:
                            if sev == "high":
                                color_style = "background-color: rgba(239, 68, 68, 0.15); color: #EF4444;"
                            elif sev == "medium":
                                color_style = "background-color: rgba(245, 158, 11, 0.15); color: #F59E0B;"
                            else:
                                color_style = "background-color: rgba(59, 130, 246, 0.15); color: #3B82F6;"
                            
                            # Severity column is at index 1
                            styles[1] = color_style
                        return styles
                        
                    st.dataframe(
                        df_display.style.apply(style_df, axis=1),
                        use_container_width=True,
                        hide_index=True
                    )
                
                # Recommendations Expander
                with st.expander("🛠️ Prioritized Recommendations", expanded=True):
                    recs = report.get("recommendations", [])
                    if recs:
                        for idx, rec in enumerate(recs):
                            st.markdown(f"**{idx + 1}.** {rec}")
                    else:
                        st.write("No recommendations necessary.")
                        
                # Download Button
                st.markdown("---")
                json_string = json.dumps(report, indent=4)
                st.download_button(
                    label="📥 Download Full Compliance Report (JSON)",
                    data=json_string,
                    file_name=f"compliance_report_{uploaded_file.name.replace('.pdf', '')}.json",
                    mime="application/json"
                )
                
        except ValueError as ve:
            if "scanned" in str(ve).lower():
                st.warning("⚠️ This PDF appears to be scanned. OCR support coming soon.")
            else:
                st.error(f"⚠️ Validation Error: {ve}")
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
            import traceback
            st.code(traceback.format_exc())
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
else:
    # Clean UI guidance card
    st.info("💡 Please upload a compliance document PDF in the field above. "
            "You can click '📚 Load Mock Regulatory Rules' in the sidebar to test retrieval, "
            "then upload a document describing your policies (e.g. storage of plain passwords to trigger REG-101).")
