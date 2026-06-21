from crewai import Agent, LLM

def get_legal_auditor_agent(llm: LLM) -> Agent:
    """Creates and returns the Legal Auditor agent."""
    return Agent(
        role="Legal Auditor",
        goal="Receive the compliance checker's findings and apply legal reasoning — confirm which are genuine violations, assess legal risk, and suggest corrective actions for each.",
        backstory=(
            "You are a legal auditor. Your job is to review the compliance checker's "
            "findings and apply legal reasoning to confirm which are genuine violations, "
            "assess the legal risk, and suggest corrective actions for each finding."
        ),
        tools=[],
        llm=llm,
        verbose=True
    )
