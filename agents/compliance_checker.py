from crewai import Agent, LLM
from pipeline.retriever import retrieve
import config

def get_compliance_checker_agent(llm: LLM, client=None, collection_name: str = None) -> Agent:
    """Creates and returns the Compliance Checker agent."""
    
    from crewai.tools import tool
    
    @tool("Retrieve Regulatory Rules")
    def retrieve_rules(query: str) -> str:
        """Search and retrieve relevant regulatory compliance rules, guidelines, or policies from the vector database for a given query."""
        results = retrieve(query, client=client, collection_name=collection_name, top_k=config.TOP_K_RESULTS)
        if not results:
            return "No relevant regulatory rules found in the database. Please ensure reference regulatory documents are uploaded."
        
        formatted = []
        for i, r in enumerate(results):
            formatted.append(
                f"Result {i+1}:\n"
                f"Source: {r['metadata']['source_file']} (Page {r['metadata']['page_number']})\n"
                f"Content: {r['text']}\n"
                f"Match Score: {r['score']:.4f}\n"
                f"----------------------------------------"
            )
        return "\n".join(formatted)

    return Agent(
        role="Compliance Checker",
        goal="Read the uploaded document section by section, retrieve relevant regulatory rules from the vector DB, and flag any potential violations with the exact text passage and rule violated.",
        backstory=(
            "You are a senior compliance analyst. Your only job is to identify "
            "passages in the provided document that may violate the regulatory "
            "rules retrieved from the knowledge base. Be precise. Cite the exact "
            "text. Do not guess — if you are unsure, mark severity as low."
        ),
        tools=[retrieve_rules],
        llm=llm,
        verbose=True
    )

