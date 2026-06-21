"""
verify.py -- Quick syntax and import verification script.
Run from inside compliance_auditor/ directory:
    python verify.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Verifying imports...")

errors = []

try:
    import config
    print(f"  [OK] config -- CHUNK_SIZE={config.CHUNK_SIZE}, MODEL={config.EMBEDDING_MODEL}")
except Exception as e:
    errors.append(f"  [FAIL] config: {e}")
    print(errors[-1])

try:
    from pipeline.ingestion import ingest_pdf, get_qdrant_client, get_embedding_model, clear_db, reset_qdrant_client
    print("  [OK] pipeline.ingestion")
except Exception as e:
    errors.append(f"  [FAIL] pipeline.ingestion: {e}")
    print(errors[-1])

try:
    from pipeline.retriever import retrieve
    print("  [OK] pipeline.retriever")
except Exception as e:
    errors.append(f"  [FAIL] pipeline.retriever: {e}")
    print(errors[-1])

try:
    from agents.compliance_checker import get_compliance_checker_agent
    print("  [OK] agents.compliance_checker")
except Exception as e:
    errors.append(f"  [FAIL] agents.compliance_checker: {e}")
    print(errors[-1])

try:
    from agents.legal_auditor import get_legal_auditor_agent
    print("  [OK] agents.legal_auditor")
except Exception as e:
    errors.append(f"  [FAIL] agents.legal_auditor: {e}")
    print(errors[-1])

try:
    from agents.report_compiler import get_report_compiler_agent
    print("  [OK] agents.report_compiler")
except Exception as e:
    errors.append(f"  [FAIL] agents.report_compiler: {e}")
    print(errors[-1])

try:
    import crew
    print("  [OK] crew")
except Exception as e:
    errors.append(f"  [FAIL] crew: {e}")
    print(errors[-1])

print()
if not errors:
    print("[PASS] All modules verified successfully!")
    print()
    print("Next steps:")
    print("  1. Copy .env.example to .env and add your ANTHROPIC_API_KEY")
    print("  2. Run: streamlit run app.py")
else:
    print(f"[FAIL] {len(errors)} error(s) found. Please fix before running the application.")
    sys.exit(1)
