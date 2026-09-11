"""
Unit and integration tests for SynkAI Sprint 4 Multi-Agent Meeting Intelligence.
Tests Parser, Summary, Action Item, Decision, Deadline, Risk, and Coordinator agents,
the LangGraph workflow, the MeetingAnalysisService, and the FastAPI /meeting/analyze endpoint.

Also covers the Sprint 4 reliability fixes: deterministic (LLM-free) parsing, strictly
sequential agent execution against the local Ollama server, and explicit agent failures.
"""

import json
import threading
import time
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.agents import (
    AgentExecutionError,
    ParserAgent,
    SummaryAgent,
    ActionItemAgent,
    DecisionAgent,
    DeadlineAgent,
    RiskAgent,
    CoordinatorAgent
)
from backend.services.meeting_analysis_service import MeetingAnalysisService
from backend.services.ollama_gate import OllamaBusyError, OllamaGate
from backend.models.analysis import MeetingAnalysisResponse

client = TestClient(app)

TRANSCRIPT = "Alice: Bob is implementing embeddings by Friday."


# Helper function to mock Ollama Service generation responses
def mock_generate_side_effect(
    prompt: str,
    system_prompt: str = "",
    json_format: bool = False,
    label: str = None
) -> str:
    system_prompt_lower = system_prompt.lower()
    if "meeting summary" in system_prompt_lower:
        return json.dumps({
            "executive_summary": "Alice and Bob discussed roadmap planning.",
            "meeting_overview": "Overview of meeting discussion on embeddings timeline."
        })
    elif "action item" in system_prompt_lower:
        return json.dumps({
            "action_items": [
                {
                    "task": "Implement embeddings",
                    "owner": "Bob",
                    "status": "Pending",
                    "priority": "High",
                    "due_date": "Friday"
                }
            ]
        })
    elif "decision" in system_prompt_lower:
        return json.dumps({
            "decisions": [
                "Decided to use ChromaDB",
                "Agreed on Python 3.13"
            ]
        })
    elif "deadline" in system_prompt_lower:
        return json.dumps({
            "deadlines": [
                {
                    "deadline": "Friday deadline",
                    "date": "Friday",
                    "milestone": "Implement embeddings",
                    "responsible_person": "Bob"
                }
            ]
        })
    elif "risk" in system_prompt_lower:
        return json.dumps({
            "risks": [
                {
                    "risk": "Ollama network timeout risk",
                    "blocker": "Server downtime",
                    "dependency": "Ollama running locally",
                    "unresolved_issue": None
                }
            ]
        })
    return "{}"


@patch("backend.services.ollama_service.OllamaService.generate", side_effect=mock_generate_side_effect)
def test_individual_agents(mock_gen):
    """
    Tests each individual agent's processing capability.
    """
    # Test Parser Agent (deterministic, no LLM call)
    parser = ParserAgent()
    cleaned = parser.process("[00:01]  Alice  :   Bob is implementing embeddings by Friday.  ")
    assert cleaned == "Alice: Bob is implementing embeddings by Friday."

    # Test Summary Agent
    summary_agent = SummaryAgent()
    summary = summary_agent.process(cleaned)
    assert summary["executive_summary"] == "Alice and Bob discussed roadmap planning."
    assert summary["meeting_overview"] == "Overview of meeting discussion on embeddings timeline."

    # Test Action Item Agent
    action_agent = ActionItemAgent()
    actions = action_agent.process(cleaned)
    assert len(actions) == 1
    assert actions[0]["task"] == "Implement embeddings"
    assert actions[0]["owner"] == "Bob"

    # Test Decision Agent
    decision_agent = DecisionAgent()
    decisions = decision_agent.process(cleaned)
    assert len(decisions) == 2
    assert "Decided to use ChromaDB" in decisions

    # Test Deadline Agent
    deadline_agent = DeadlineAgent()
    deadlines = deadline_agent.process(cleaned)
    assert len(deadlines) == 1
    assert deadlines[0]["date"] == "Friday"

    # Test Risk Agent
    risk_agent = RiskAgent()
    risks = risk_agent.process(cleaned)
    assert len(risks) == 1
    assert risks[0]["risk"] == "Ollama network timeout risk"

    # Test Coordinator Agent
    coordinator = CoordinatorAgent()
    final_output = coordinator.process(
        summary_data=summary,
        action_items=actions,
        decisions=decisions,
        deadlines=deadlines,
        risks=risks
    )
    assert isinstance(final_output, MeetingAnalysisResponse)
    assert final_output.executive_summary == "Alice and Bob discussed roadmap planning."
    assert len(final_output.action_items) == 1
    assert final_output.action_items[0].owner == "Bob"
    assert final_output.action_items[0].task == "Implement embeddings"
    assert len(final_output.decisions) == 2
    assert len(final_output.deadlines) == 1
    assert len(final_output.risks) == 1
    assert final_output.analysis_complete is True
    assert final_output.agent_errors == []


@patch("backend.services.ollama_service.OllamaService.generate", side_effect=mock_generate_side_effect)
def test_parser_agent_makes_no_llm_call(mock_gen):
    """
    The Parser Agent must clean transcripts in pure Python: transcript normalization needs
    no reasoning, and an extra qwen3 call per analysis is exactly what overloaded Ollama.
    """
    raw = (
        "[00:00:12] Sarah: Let's start the Sprint 4 planning meeting.\n"
        "\n"
        "  \n"
        "--- Page 2 ---\n"
        "10:15 Mike : I will implement the LangGraph workflow.   \n"
        "Mike : I will implement the LangGraph workflow.\n"
        "Emily: [inaudible] I'll build the Action Item Agent.\n"
    )

    cleaned = ParserAgent().process(raw)

    assert mock_gen.call_count == 0, "Parser Agent must not call the LLM"
    assert cleaned.splitlines() == [
        "Sarah: Let's start the Sprint 4 planning meeting.",
        "Mike: I will implement the LangGraph workflow.",
        "Emily: I'll build the Action Item Agent.",
    ]


def test_parser_agent_rejects_empty_transcript():
    """
    An unusable transcript is an explicit failure, not an empty success.
    """
    with pytest.raises(AgentExecutionError) as exc_info:
        ParserAgent().process("   \n\n  ")
    assert exc_info.value.agent == "parser_agent"


@patch("backend.services.ollama_service.OllamaService.generate", side_effect=mock_generate_side_effect)
def test_meeting_analysis_service_workflow(mock_gen):
    """
    Tests that the MeetingAnalysisService runs the entire LangGraph workflow successfully.
    """
    service = MeetingAnalysisService()
    result = service.analyze_transcript("Sample meeting notes")

    assert isinstance(result, MeetingAnalysisResponse)
    assert result.executive_summary == "Alice and Bob discussed roadmap planning."
    assert len(result.action_items) == 1
    assert result.action_items[0].owner == "Bob"
    assert len(result.decisions) == 2
    assert len(result.deadlines) == 1
    assert len(result.risks) == 1
    assert result.analysis_complete is True

    # One LLM call per LLM-backed agent: summary, action_item, decision, deadline, risk.
    assert mock_gen.call_count == 5


def test_workflow_runs_agents_sequentially():
    """
    Guards the primary Sprint 4 fix: the LangGraph workflow must never have two LLM agents
    in flight at once, otherwise the local Ollama server times out.
    """
    in_flight = 0
    max_in_flight = 0
    lock = threading.Lock()

    def slow_generate(prompt, system_prompt="", json_format=False, label=None):
        nonlocal in_flight, max_in_flight
        with lock:
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
        try:
            time.sleep(0.05)
            return mock_generate_side_effect(prompt, system_prompt, json_format, label)
        finally:
            with lock:
                in_flight -= 1

    with patch("backend.services.ollama_service.OllamaService.generate", side_effect=slow_generate):
        result = MeetingAnalysisService().analyze_transcript(TRANSCRIPT)

    assert max_in_flight == 1, f"Expected sequential LLM execution, saw {max_in_flight} concurrent calls"
    assert result.analysis_complete is True


def test_ollama_gate_serializes_concurrent_callers():
    """
    The shared gate must also bound concurrency across requests (e.g. a RAG chat query
    arriving while the agent workflow is running).
    """
    gate = OllamaGate(max_concurrency=1, queue_timeout=5)
    in_flight = 0
    max_in_flight = 0
    lock = threading.Lock()

    def worker():
        nonlocal in_flight, max_in_flight
        with gate.slot("test-worker"):
            with lock:
                in_flight += 1
                max_in_flight = max(max_in_flight, in_flight)
            time.sleep(0.05)
            with lock:
                in_flight -= 1

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert max_in_flight == 1


def test_ollama_gate_raises_when_no_slot_frees_up():
    """
    Waiting forever is not an option either: a starved caller must fail loudly.
    """
    gate = OllamaGate(max_concurrency=1, queue_timeout=0)

    with gate.slot("holder"):
        with pytest.raises(OllamaBusyError):
            with gate.slot("waiter"):
                pass


class FakeStreamResponse:
    """Minimal stand-in for a streaming `requests` response from /api/generate."""

    status_code = 200

    def __init__(self, pieces, done=True):
        self._lines = [json.dumps({"response": piece, "done": False}) for piece in pieces]
        if done:
            self._lines.append(json.dumps({"response": "", "done": True}))

    def iter_lines(self, decode_unicode=False):
        return iter(self._lines)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_generate_streams_and_bounds_the_request():
    """
    Guards the request-level reliability settings: streaming (so the timeout detects a
    stalled server rather than a slow one), thinking disabled (measured ~16x faster on a
    free-form qwen3 call), a resident model, and a hard cap on generated tokens.
    """
    from backend.services.ollama_service import OllamaService

    response = FakeStreamResponse(["Hello", " world"])
    with patch("backend.services.ollama_service.requests.post", return_value=response) as mock_post:
        answer = OllamaService().generate("hello", system_prompt="be brief", label="unit-test")

    assert answer == "Hello world"
    payload = mock_post.call_args.kwargs["json"]
    assert payload["stream"] is True
    assert payload["think"] is False
    assert payload["keep_alive"]
    assert payload["options"]["num_predict"] > 0
    assert mock_post.call_args.kwargs["stream"] is True
    assert mock_post.call_args.kwargs["timeout"] > 0


@pytest.mark.parametrize("stream_error", [
    # requests raises ReadTimeout before the stream starts, but wraps a mid-stream read
    # timeout in ConnectionError. Both must be reported as a stalled server.
    "read_timeout",
    "connection_error",
])
def test_generate_reports_a_stalled_server(stream_error):
    """
    A server that stops producing tokens must surface as an explicit error.
    """
    import requests as requests_lib
    from backend.services.ollama_service import OllamaService

    errors = {
        "read_timeout": requests_lib.exceptions.ReadTimeout("Read timed out."),
        "connection_error": requests_lib.exceptions.ConnectionError("Read timed out."),
    }

    class StallingResponse(FakeStreamResponse):
        def iter_lines(self, decode_unicode=False):
            yield json.dumps({"response": "partial", "done": False})
            raise errors[stream_error]

    with patch("backend.services.ollama_service.requests.post", return_value=StallingResponse([])):
        with pytest.raises(ConnectionError, match="stopped responding"):
            OllamaService().generate("hello", label="unit-test")


def test_generate_strips_inline_think_blocks():
    """
    Defensive: if a reasoning model still inlines a <think> block, it must not leak into
    the JSON handed to the agents.
    """
    from backend.services.ollama_service import OllamaService

    response = FakeStreamResponse(["<think>weighing options</think>\n", '{"decisions": []}'])
    with patch("backend.services.ollama_service.requests.post", return_value=response):
        answer = OllamaService().generate("hello", json_format=True)

    assert answer == '{"decisions": []}'


def test_failed_agent_is_reported_not_silently_empty():
    """
    A timing-out agent must surface in agent_errors instead of returning an empty list
    that looks like "nothing found".
    """
    def failing_risk_agent(prompt, system_prompt="", json_format=False, label=None):
        if "risk analysis assistant" in system_prompt.lower():
            raise ConnectionError("Ollama request timed out after 180s while running 'risk_agent'.")
        return mock_generate_side_effect(prompt, system_prompt, json_format, label)

    with patch("backend.services.ollama_service.OllamaService.generate", side_effect=failing_risk_agent):
        result = MeetingAnalysisService().analyze_transcript(TRANSCRIPT)

    assert result.analysis_complete is False
    assert [err.agent for err in result.agent_errors] == ["risk_agent"]
    assert "timed out" in result.agent_errors[0].error
    # Successful agents still return their data.
    assert result.risks == []
    assert len(result.decisions) == 2
    assert len(result.action_items) == 1


def test_total_agent_failure_raises():
    """
    If every agent fails there is no analysis to report, so the workflow must error out
    rather than return an empty-but-successful payload.
    """
    def always_fail(prompt, system_prompt="", json_format=False, label=None):
        raise ConnectionError("Ollama server is unreachable at 'http://localhost:11434'.")

    with patch("backend.services.ollama_service.OllamaService.generate", side_effect=always_fail):
        with pytest.raises(RuntimeError, match="Every analysis agent failed"):
            MeetingAnalysisService().analyze_transcript(TRANSCRIPT)


def test_invalid_agent_json_is_a_failure():
    """
    Unparseable LLM output is an agent failure, not an empty result.
    """
    def bad_json(prompt, system_prompt="", json_format=False, label=None):
        if "decision" in system_prompt.lower():
            return "Sure! Here are the decisions: ..."
        return mock_generate_side_effect(prompt, system_prompt, json_format, label)

    with patch("backend.services.ollama_service.OllamaService.generate", side_effect=bad_json):
        result = MeetingAnalysisService().analyze_transcript(TRANSCRIPT)

    assert result.analysis_complete is False
    assert [err.agent for err in result.agent_errors] == ["decision_agent"]
    assert "not valid JSON" in result.agent_errors[0].error


@patch("backend.services.ollama_service.OllamaService.generate", side_effect=mock_generate_side_effect)
def test_meeting_analyze_endpoint(mock_gen):
    """
    Verifies that the POST /meeting/analyze API endpoint responds with the structured multi-agent result.
    """
    # 1. Test using transcript_text
    response = client.post(
        "/meeting/analyze",
        json={"transcript_text": "We discussed tasks. Bob is writing code. Deadline is Friday."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "executive_summary" in data
    assert data["executive_summary"] == "Alice and Bob discussed roadmap planning."
    assert len(data["action_items"]) == 1
    assert data["action_items"][0]["owner"] == "Bob"
    assert len(data["decisions"]) == 2
    assert len(data["deadlines"]) == 1
    assert len(data["risks"]) == 1
    assert data["analysis_complete"] is True
    assert data["agent_errors"] == []

    # 2. Test input validation (both missing)
    response_err = client.post("/meeting/analyze", json={})
    assert response_err.status_code == 400
    assert "Either 'document_id' or 'transcript_text' must be provided." in response_err.json()["detail"]


@patch("backend.routes.analysis._get_transcript_by_document_id")
@patch("backend.services.ollama_service.OllamaService.generate", side_effect=mock_generate_side_effect)
def test_meeting_analyze_with_document_id(mock_gen, mock_get_transcript):
    """
    Verifies that POST /meeting/analyze queries for the transcript if document_id is provided.
    """
    mock_get_transcript.return_value = "We discussed tasks. Bob is writing code. Deadline is Friday."

    response = client.post(
        "/meeting/analyze",
        json={"document_id": "test_doc_555"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["executive_summary"] == "Alice and Bob discussed roadmap planning."
    assert len(data["action_items"]) == 1
    assert data["action_items"][0]["owner"] == "Bob"
    assert len(data["decisions"]) == 2
    assert len(data["deadlines"]) == 1
    assert len(data["risks"]) == 1


def test_meeting_analyze_endpoint_reports_total_failure():
    """
    A dead Ollama server must produce a visible HTTP error, never a 200 with empty lists.
    """
    def always_fail(prompt, system_prompt="", json_format=False, label=None):
        raise ConnectionError("Ollama server is unreachable at 'http://localhost:11434'.")

    with patch("backend.services.ollama_service.OllamaService.generate", side_effect=always_fail):
        response = client.post("/meeting/analyze", json={"transcript_text": TRANSCRIPT})

    assert response.status_code == 500
    assert "Every analysis agent failed" in response.json()["detail"]
