"""
Agent error types for SynkAI Sprint 4.

Agents raise instead of returning empty results, so a failed agent is never mistaken for
an agent that legitimately found nothing. The LangGraph nodes catch these errors, record
them on the workflow state, and the Coordinator surfaces them in the API response.
"""


class AgentExecutionError(RuntimeError):
    """
    Raised when a specialized agent could not complete its task.
    """

    def __init__(self, agent: str, message: str):
        self.agent = agent
        self.message = message
        super().__init__(f"{agent} failed: {message}")
