"""
LangGraph workflow for SynkAI Sprint 4 meeting analysis.
Defines a state graph connecting Parser, Summary, Action Item, Decision, Deadline, Risk, and Coordinator agents.

Execution is a deliberate *sequential* chain:

    parser -> summary -> action_item -> decision -> deadline -> risk -> coordinator

The earlier fan-out design (parser branching into all five extraction agents) put every
LLM agent in the same LangGraph superstep, so LangGraph ran them concurrently in its thread
pool and five qwen3 generations hit the local Ollama server at once. Local Ollama serves
those by time-slicing a single model, so each request took several times longer and the HTTP
read timeout fired. Chaining the nodes keeps exactly the same specialized agents while giving
the local server one generation at a time.
"""

import operator
from typing import Annotated, TypedDict, List, Dict, Any, Callable, Optional
from langgraph.graph import StateGraph, END

from backend.agents import (
    ParserAgent,
    SummaryAgent,
    ActionItemAgent,
    DecisionAgent,
    DeadlineAgent,
    RiskAgent,
    CoordinatorAgent
)
from backend.agents.action_item_agent import AGENT_NAME as ACTION_ITEM_AGENT_NAME
from backend.agents.deadline_agent import AGENT_NAME as DEADLINE_AGENT_NAME
from backend.agents.decision_agent import AGENT_NAME as DECISION_AGENT_NAME
from backend.agents.errors import AgentExecutionError
from backend.agents.parser_agent import AGENT_NAME as PARSER_AGENT_NAME
from backend.agents.risk_agent import AGENT_NAME as RISK_AGENT_NAME
from backend.agents.summary_agent import AGENT_NAME as SUMMARY_AGENT_NAME
from backend.models.analysis import MeetingAnalysisResponse
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# The LLM-backed agents, in execution order. Used to reason about partial failures.
LLM_AGENT_NAMES = (
    SUMMARY_AGENT_NAME,
    ACTION_ITEM_AGENT_NAME,
    DECISION_AGENT_NAME,
    DEADLINE_AGENT_NAME,
    RISK_AGENT_NAME,
)


class MeetingState(TypedDict):
    """
    Shared state schema for the LangGraph meeting workflow.
    """
    transcript: str
    parsed_transcript: str
    summary_data: Dict[str, Any]
    action_items: List[Dict[str, Any]]
    decisions: List[str]
    deadlines: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    # Accumulated with operator.add so every node can append without clobbering peers.
    agent_errors: Annotated[List[Dict[str, str]], operator.add]
    final_analysis: Optional[MeetingAnalysisResponse]


def _run_agent_node(
    node_name: str,
    state_key: str,
    runner: Callable[[], Any]
) -> Dict[str, Any]:
    """
    Executes one agent and translates an AgentExecutionError into an explicit state record.

    A failing agent contributes an entry to `agent_errors` and leaves its own state key
    untouched, so the response can distinguish "this agent failed" from "this agent found
    nothing". Unexpected (non-agent) exceptions are left to propagate and fail the workflow.

    Args:
        node_name (str): LangGraph node name, used for logging and error reporting.
        state_key (str): State key the agent's successful output is written to.
        runner (Callable[[], Any]): Zero-argument callable invoking the agent.

    Returns:
        Dict[str, Any]: State update for this node.
    """
    logger.info(f"{node_name} node execution started.")
    try:
        result = runner()
    except AgentExecutionError as exc:
        logger.error(f"{node_name} node FAILED: {exc.message}")
        return {"agent_errors": [{"agent": exc.agent, "error": exc.message}]}

    logger.info(f"{node_name} node execution completed.")
    return {state_key: result}


# Node execution helpers
def run_parser(state: MeetingState) -> Dict[str, Any]:
    agent = ParserAgent()
    return _run_agent_node(
        "Parser Agent",
        "parsed_transcript",
        lambda: agent.process(state.get("transcript", ""))
    )


def run_summary(state: MeetingState) -> Dict[str, Any]:
    agent = SummaryAgent()
    return _run_agent_node(
        "Summary Agent",
        "summary_data",
        lambda: agent.process(state.get("parsed_transcript", ""))
    )


def run_action_item(state: MeetingState) -> Dict[str, Any]:
    agent = ActionItemAgent()
    return _run_agent_node(
        "Action Item Agent",
        "action_items",
        lambda: agent.process(state.get("parsed_transcript", ""))
    )


def run_decision(state: MeetingState) -> Dict[str, Any]:
    agent = DecisionAgent()
    return _run_agent_node(
        "Decision Agent",
        "decisions",
        lambda: agent.process(state.get("parsed_transcript", ""))
    )


def run_deadline(state: MeetingState) -> Dict[str, Any]:
    agent = DeadlineAgent()
    return _run_agent_node(
        "Deadline Agent",
        "deadlines",
        lambda: agent.process(state.get("parsed_transcript", ""))
    )


def run_risk(state: MeetingState) -> Dict[str, Any]:
    agent = RiskAgent()
    return _run_agent_node(
        "Risk Agent",
        "risks",
        lambda: agent.process(state.get("parsed_transcript", ""))
    )


def route_after_parser(state: MeetingState) -> str:
    """
    Routes to the extraction agents only if the Parser Agent produced usable text.

    Without this guard a parser failure would cascade into five identical
    "empty transcript" agent failures instead of one clear root cause.
    """
    if (state.get("parsed_transcript") or "").strip():
        return "summary"

    logger.error("Parser produced no transcript; skipping extraction agents.")
    return "coordinator"


def run_coordinator(state: MeetingState) -> Dict[str, Any]:
    logger.info("Coordinator Agent node execution started.")
    agent = CoordinatorAgent()
    final_analysis = agent.process(
        summary_data=state.get("summary_data") or {},
        action_items=state.get("action_items") or [],
        decisions=state.get("decisions") or [],
        deadlines=state.get("deadlines") or [],
        risks=state.get("risks") or [],
        agent_errors=state.get("agent_errors") or []
    )
    logger.info("Coordinator Agent node execution completed.")
    return {"final_analysis": final_analysis}


def create_meeting_graph() -> StateGraph:
    """
    Compiles and returns the LangGraph workflow graph for meeting analysis.

    The nodes form a single sequential chain so that at most one agent performs local LLM
    inference at any moment.
    """
    # Create StateGraph
    workflow = StateGraph(MeetingState)

    # Add Nodes
    workflow.add_node("parser", run_parser)
    workflow.add_node("summary", run_summary)
    workflow.add_node("action_item", run_action_item)
    workflow.add_node("decision", run_decision)
    workflow.add_node("deadline", run_deadline)
    workflow.add_node("risk", run_risk)
    workflow.add_node("coordinator", run_coordinator)

    # Set Entry Point
    workflow.set_entry_point("parser")

    # Define Graph Edges: one agent at a time, so the local Ollama server is never
    # asked to run several qwen3 generations in parallel.
    workflow.add_conditional_edges(
        "parser",
        route_after_parser,
        {"summary": "summary", "coordinator": "coordinator"}
    )
    workflow.add_edge("summary", "action_item")
    workflow.add_edge("action_item", "decision")
    workflow.add_edge("decision", "deadline")
    workflow.add_edge("deadline", "risk")
    workflow.add_edge("risk", "coordinator")

    # Coordinator routes to END
    workflow.add_edge("coordinator", END)

    return workflow.compile()
