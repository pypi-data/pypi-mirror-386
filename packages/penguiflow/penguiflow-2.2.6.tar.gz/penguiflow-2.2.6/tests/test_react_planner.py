from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Mapping
from typing import Any

import pytest
from pydantic import BaseModel

from penguiflow.catalog import build_catalog, tool
from penguiflow.node import Node
from penguiflow.planner import PlannerPause, ReactPlanner
from penguiflow.planner.react import Trajectory
from penguiflow.registry import ModelRegistry


class Query(BaseModel):
    question: str


class Intent(BaseModel):
    intent: str


class Documents(BaseModel):
    documents: list[str]


class Answer(BaseModel):
    answer: str


class ShardRequest(BaseModel):
    topic: str
    shard: int


class ShardPayload(BaseModel):
    shard: int
    text: str


class MergeArgs(BaseModel):
    expect: int
    results: list[ShardPayload]


class AuditArgs(BaseModel):
    branches: list[dict[str, Any]]
    failures: list[dict[str, Any]]


@tool(desc="Detect intent", tags=["nlp"])
async def triage(args: Query, ctx: object) -> Intent:
    return Intent(intent="docs")


@tool(desc="Search knowledge base", side_effects="read")
async def retrieve(args: Intent, ctx: object) -> Documents:
    return Documents(documents=[f"Answering about {args.intent}"])


@tool(desc="Compose final answer")
async def respond(args: Answer, ctx: object) -> Answer:
    return args


@tool(desc="Return invalid documents")
async def broken(args: Intent, ctx: object) -> Documents:  # type: ignore[return-type]
    return "boom"  # type: ignore[return-value]


@tool(desc="Fetch documents from primary shard", tags=["parallel"])
async def fetch_primary(args: ShardRequest, ctx: Any) -> ShardPayload:
    await asyncio.sleep(0.05)
    return ShardPayload(shard=args.shard, text=f"{args.topic}-primary")


@tool(desc="Fetch documents from secondary shard", tags=["parallel"])
async def fetch_secondary(args: ShardRequest, ctx: Any) -> ShardPayload:
    await asyncio.sleep(0.05)
    return ShardPayload(shard=args.shard, text=f"{args.topic}-secondary")


@tool(desc="Merge shard payloads")
async def merge_results(args: MergeArgs, ctx: Any) -> Documents:
    assert ctx.meta.get("parallel_success_count") == args.expect
    assert len(ctx.meta.get("parallel_results", [])) == args.expect
    return Documents(documents=[item.text for item in args.results])


AUDIT_CALLS: list[dict[str, Any]] = []


@tool(desc="Audit failed branches")
async def audit_parallel(args: AuditArgs, ctx: Any) -> Documents:
    AUDIT_CALLS.append(args.model_dump())
    return Documents(documents=[f"{len(args.failures)} failures"])


@tool(desc="Approval required before proceeding")
async def approval_gate(args: Intent, ctx: Any) -> Intent:
    await ctx.pause("approval_required", {"intent": args.intent})
    return args


class PlannerTimeout(RuntimeError):
    def __init__(self, message: str, suggestion: str) -> None:
        super().__init__(message)
        self.suggestion = suggestion


@tool(desc="Remote fetch that may timeout", side_effects="external")
async def unstable(args: Intent, ctx: object) -> Documents:
    raise PlannerTimeout("upstream timeout", "use_cache")


@tool(desc="Use cached retrieval", side_effects="read")
async def cached(args: Intent, ctx: object) -> Documents:
    return Documents(documents=[f"Cached docs for {args.intent}"])


class StubClient:
    def __init__(self, responses: list[Mapping[str, object]]) -> None:
        self._responses = [json.dumps(item) for item in responses]
        self.calls: list[list[Mapping[str, str]]] = []

    async def complete(
        self,
        *,
        messages: list[Mapping[str, str]],
        response_format: Mapping[str, object] | None = None,
    ) -> str:
        self.calls.append(list(messages))
        if not self._responses:
            raise AssertionError("No stub responses left")
        return self._responses.pop(0)


class SummarizerStub:
    def __init__(self) -> None:
        self.calls: list[list[Mapping[str, str]]] = []

    async def complete(
        self,
        *,
        messages: list[Mapping[str, str]],
        response_format: Mapping[str, object] | None = None,
    ) -> str:
        self.calls.append(list(messages))
        return json.dumps(
            {
                "goals": ["stub"],
                "facts": {"note": "compact"},
                "pending": [],
                "last_output_digest": "stub",
                "note": "stub",
            }
        )


def make_planner(client: StubClient, **kwargs: object) -> ReactPlanner:
    registry = ModelRegistry()
    registry.register("triage", Query, Intent)
    registry.register("retrieve", Intent, Documents)
    registry.register("respond", Answer, Answer)
    registry.register("broken", Intent, Documents)

    nodes = [
        Node(triage, name="triage"),
        Node(retrieve, name="retrieve"),
        Node(respond, name="respond"),
        Node(broken, name="broken"),
    ]
    catalog = build_catalog(nodes, registry)
    return ReactPlanner(llm_client=client, catalog=catalog, **kwargs)


@pytest.mark.asyncio()
async def test_react_planner_runs_end_to_end() -> None:
    client = StubClient(
        [
            {
                "thought": "triage",
                "next_node": "triage",
                "args": {"question": "What is PenguiFlow?"},
            },
            {
                "thought": "retrieve",
                "next_node": "retrieve",
                "args": {"intent": "docs"},
            },
            {
                "thought": "final",
                "next_node": None,
                "args": {"answer": "PenguiFlow is lightweight."},
            },
        ]
    )
    planner = make_planner(client)

    result = await planner.run("Tell me about PenguiFlow")

    assert result.reason == "answer_complete"
    assert result.payload == {"answer": "PenguiFlow is lightweight."}
    assert result.metadata["step_count"] == 2


@pytest.mark.asyncio()
async def test_react_planner_recovers_from_invalid_node() -> None:
    client = StubClient(
        [
            {"thought": "invalid", "next_node": "missing", "args": {}},
            {"thought": "triage", "next_node": "triage", "args": {"question": "What?"}},
            {"thought": "finish", "next_node": None, "args": {"answer": "done"}},
        ]
    )
    planner = make_planner(client)

    result = await planner.run("Test invalid node")

    assert result.reason == "answer_complete"
    assert any("missing" in step["error"] for step in result.metadata["steps"])


@pytest.mark.asyncio()
async def test_react_planner_reports_validation_error() -> None:
    client = StubClient(
        [
            {"thought": "bad", "next_node": "retrieve", "args": {}},
            {
                "thought": "triage",
                "next_node": "triage",
                "args": {"question": "Q"},
            },
            {
                "thought": "retrieve",
                "next_node": "retrieve",
                "args": {"intent": "docs"},
            },
            {"thought": "finish", "next_node": None, "args": {"answer": "ok"}},
        ]
    )
    planner = make_planner(client)

    result = await planner.run("Test validation path")

    errors = [step["error"] for step in result.metadata["steps"] if step["error"]]
    assert any("did not validate" in err for err in errors)


@pytest.mark.asyncio()
async def test_react_planner_reports_output_validation_error() -> None:
    client = StubClient(
        [
            {
                "thought": "broken",
                "next_node": "broken",
                "args": {"intent": "docs"},
            },
            {"thought": "finish", "next_node": None, "args": {"answer": "fallback"}},
        ]
    )
    registry = ModelRegistry()
    registry.register("broken", Intent, Documents)
    catalog = build_catalog([Node(broken, name="broken")], registry)
    planner = ReactPlanner(llm_client=client, catalog=catalog)

    result = await planner.run("Test output validation path")

    errors = [step["error"] for step in result.metadata["steps"] if step["error"]]
    assert any("returned data" in err for err in errors)


@pytest.mark.asyncio()
async def test_react_planner_replans_after_tool_failure() -> None:
    client = StubClient(
        [
            {
                "thought": "triage",
                "next_node": "triage",
                "args": {"question": "Need docs"},
            },
            {
                "thought": "remote",
                "next_node": "unstable",
                "args": {"intent": "docs"},
            },
            {
                "thought": "fallback",
                "next_node": "cached",
                "args": {"intent": "docs"},
            },
            {
                "thought": "wrap",
                "next_node": "respond",
                "args": {"answer": "Using cached docs"},
            },
            {
                "thought": "final",
                "next_node": None,
                "args": {"answer": "Using cached docs"},
            },
        ]
    )

    registry = ModelRegistry()
    registry.register("triage", Query, Intent)
    registry.register("unstable", Intent, Documents)
    registry.register("cached", Intent, Documents)
    registry.register("respond", Answer, Answer)

    nodes = [
        Node(triage, name="triage"),
        Node(unstable, name="unstable"),
        Node(cached, name="cached"),
        Node(respond, name="respond"),
    ]

    planner = ReactPlanner(
        llm_client=client,
        catalog=build_catalog(nodes, registry),
        max_iters=5,
    )

    result = await planner.run("Fetch docs with fallback")

    assert result.reason == "answer_complete"
    failure_step = next(
        (step for step in result.metadata["steps"] if step.get("failure")),
        None,
    )
    assert failure_step is not None
    assert failure_step["failure"]["node"] == "unstable"

    failure_prompt = json.loads(client.calls[2][-1]["content"])
    assert failure_prompt["failure"]["suggestion"] == "use_cache"
    assert failure_prompt["failure"]["error_code"] == "PlannerTimeout"


def test_react_planner_requires_catalog_or_nodes() -> None:
    client = StubClient([])
    with pytest.raises(ValueError):
        ReactPlanner(llm_client=client)


def test_react_planner_requires_llm_or_client() -> None:
    registry = ModelRegistry()
    registry.register("triage", Query, Intent)
    nodes = [Node(triage, name="triage")]
    with pytest.raises(ValueError):
        ReactPlanner(nodes=nodes, registry=registry)


@pytest.mark.asyncio()
async def test_react_planner_iteration_limit_returns_no_path() -> None:
    client = StubClient(
        [
            {
                "thought": "loop",
                "next_node": "triage",
                "args": {"question": "still thinking"},
            }
        ]
    )
    registry = ModelRegistry()
    registry.register("triage", Query, Intent)
    planner = ReactPlanner(
        llm_client=client,
        catalog=build_catalog([Node(triage, name="triage")], registry),
        max_iters=1,
    )

    result = await planner.run("Explain")
    assert result.reason == "no_path"


@pytest.mark.asyncio()
async def test_react_planner_enforces_hop_budget_limits() -> None:
    client = StubClient(
        [
            {
                "thought": "triage",
                "next_node": "triage",
                "args": {"question": "Budget"},
            },
            {
                "thought": "still need",
                "next_node": "retrieve",
                "args": {"intent": "docs"},
            },
            {
                "thought": "retry",
                "next_node": "retrieve",
                "args": {"intent": "docs"},
            },
        ]
    )

    registry = ModelRegistry()
    registry.register("triage", Query, Intent)
    registry.register("retrieve", Intent, Documents)

    nodes = [
        Node(triage, name="triage"),
        Node(retrieve, name="retrieve"),
    ]

    planner = ReactPlanner(
        llm_client=client,
        catalog=build_catalog(nodes, registry),
        hop_budget=1,
        max_iters=3,
    )

    result = await planner.run("Constrained plan")

    assert result.reason == "budget_exhausted"
    constraints = result.metadata["constraints"]
    assert constraints["hop_exhausted"] is True
    violation = json.loads(client.calls[2][-1]["content"])
    assert "Hop budget" in violation["error"]


@pytest.mark.asyncio()
async def test_react_planner_litellm_guard_raises_runtime_error() -> None:
    litellm = pytest.importorskip("litellm")

    registry = ModelRegistry()
    registry.register("triage", Query, Intent)
    nodes = [Node(triage, name="triage")]
    planner = ReactPlanner(llm="dummy", nodes=nodes, registry=registry)
    trajectory = Trajectory(query="hi")
    # When litellm is installed, it raises BadRequestError for invalid model names
    with pytest.raises((RuntimeError, litellm.exceptions.BadRequestError)) as exc:
        await planner.step(trajectory)
    # Accept either error message
    assert (
        "LiteLLM is not installed" in str(exc.value)
        or "LLM Provider NOT provided" in str(exc.value)
    )


@pytest.mark.asyncio()
async def test_react_planner_step_repairs_invalid_action() -> None:
    client = StubClient(
        [
            "{}",
            {
                "thought": "recover",
                "next_node": "triage",
                "args": {"question": "fixed"},
            },
        ]
    )
    planner = make_planner(client)
    trajectory = Trajectory(query="recover")

    action = await planner.step(trajectory)
    assert action.next_node == "triage"
    assert len(client.calls) == 2
    repair_message = client.calls[1][-1]["content"]
    assert "invalid JSON" in repair_message


@pytest.mark.asyncio()
async def test_react_planner_compacts_history_when_budget_exceeded() -> None:
    long_answer = "PenguiFlow " * 30
    client = StubClient(
        [
            {
                "thought": "triage",
                "next_node": "triage",
                "args": {"question": "What is the plan?"},
            },
            {
                "thought": "respond",
                "next_node": "respond",
                "args": {"answer": long_answer},
            },
            {"thought": "finish", "next_node": None, "args": {"answer": "done"}},
        ]
    )
    planner = make_planner(client, token_budget=180)

    result = await planner.run("Explain budget handling")

    assert result.reason == "answer_complete"
    assert any(
        msg["role"] == "system" and "Trajectory summary" in msg["content"]
        for msg in client.calls[1]
    )


@pytest.mark.asyncio()
async def test_react_planner_invokes_summarizer_client() -> None:
    client = StubClient(
        [
            {
                "thought": "triage",
                "next_node": "triage",
                "args": {"question": "Summarise"},
            },
            {
                "thought": "respond",
                "next_node": "respond",
                "args": {"answer": "value"},
            },
            {"thought": "finish", "next_node": None, "args": {"answer": "ok"}},
        ]
    )
    planner = make_planner(client, token_budget=60)
    summarizer = SummarizerStub()
    planner._summarizer_client = summarizer  # type: ignore[attr-defined]

    await planner.run("Trigger summariser")

    assert summarizer.calls, "Expected summarizer to be invoked"


@pytest.mark.asyncio()
async def test_react_planner_pause_and_resume_flow() -> None:
    registry = ModelRegistry()
    registry.register("triage", Query, Intent)
    registry.register("approval", Intent, Intent)
    registry.register("retrieve", Intent, Documents)
    registry.register("respond", Answer, Answer)

    nodes = [
        Node(triage, name="triage"),
        Node(approval_gate, name="approval"),
        Node(retrieve, name="retrieve"),
        Node(respond, name="respond"),
    ]
    catalog = build_catalog(nodes, registry)

    client = StubClient(
        [
            {
                "thought": "triage",
                "next_node": "triage",
                "args": {"question": "Send report"},
            },
            {
                "thought": "approval",
                "next_node": "approval",
                "args": {"intent": "docs"},
            },
            {
                "thought": "retrieve",
                "next_node": "retrieve",
                "args": {"intent": "docs"},
            },
            {
                "thought": "finish",
                "next_node": None,
                "args": {"answer": "Report sent"},
            },
        ]
    )
    planner = ReactPlanner(llm_client=client, catalog=catalog, pause_enabled=True)

    pause_result = await planner.run("Share metrics with approval")
    assert isinstance(pause_result, PlannerPause)
    assert pause_result.reason == "approval_required"

    resume_result = await planner.resume(
        pause_result.resume_token,
        user_input="approved",
    )
    assert resume_result.reason == "answer_complete"

    post_pause_calls = client.calls[2:]
    assert any(
        "Resume input" in msg["content"]
        for call in post_pause_calls
        for msg in call
    )


@pytest.mark.asyncio()
async def test_react_planner_resume_preserves_hop_budget() -> None:
    registry = ModelRegistry()
    registry.register("approval", Intent, Intent)
    registry.register("respond", Answer, Answer)

    nodes = [
        Node(approval_gate, name="approval"),
        Node(respond, name="respond"),
    ]
    catalog = build_catalog(nodes, registry)

    client = StubClient(
        [
            {
                "thought": "request approval",
                "next_node": "approval",
                "args": {"intent": "docs"},
            },
            {
                "thought": "follow up",
                "next_node": "respond",
                "args": {"answer": "Report"},
            },
            {
                "thought": "finish",
                "next_node": None,
                "args": {"answer": "Report"},
            },
        ]
    )

    planner = ReactPlanner(
        llm_client=client,
        catalog=catalog,
        pause_enabled=True,
        hop_budget=1,
    )

    pause_result = await planner.run("Send report with approval")
    assert isinstance(pause_result, PlannerPause)
    assert pause_result.reason == "approval_required"

    resume_result = await planner.resume(
        pause_result.resume_token,
        user_input="approved",
    )
    assert resume_result.reason == "answer_complete"

    steps = resume_result.metadata["steps"]
    assert any(
        step.get("error") and "Hop budget" in step["error"]
        for step in steps
    ), "expected hop budget violation after resume"

    constraints = resume_result.metadata["constraints"]
    assert constraints["hops_used"] == 1
    assert constraints["hop_exhausted"] is True


@pytest.mark.asyncio()
async def test_react_planner_disallows_nodes_from_hints() -> None:
    client = StubClient(
        [
            {
                "thought": "bad",
                "next_node": "broken",
                "args": {"intent": "docs"},
            },
            {
                "thought": "triage",
                "next_node": "triage",
                "args": {"question": "Hi"},
            },
            {
                "thought": "finish",
                "next_node": None,
                "args": {"answer": "done"},
            },
        ]
    )
    planner = make_planner(client, planning_hints={"disallow_nodes": ["broken"]})

    result = await planner.run("test hints")

    assert result.reason == "answer_complete"
    assert any(
        msg["role"] == "user" and "not permitted" in msg["content"]
        for msg in client.calls[1]
    )


@pytest.mark.asyncio()
async def test_react_planner_emits_ordering_hint_once() -> None:
    client = StubClient(
        [
            {
                "thought": "early",
                "next_node": "retrieve",
                "args": {"intent": "docs"},
            },
            {
                "thought": "triage",
                "next_node": "triage",
                "args": {"question": "Order?"},
            },
            {
                "thought": "retrieve",
                "next_node": "retrieve",
                "args": {"intent": "docs"},
            },
            {
                "thought": "finish",
                "next_node": None,
                "args": {"answer": "done"},
            },
        ]
    )
    planner = make_planner(
        client,
        planning_hints={"ordering_hints": ["triage", "retrieve"]},
    )

    result = await planner.run("ordering")

    assert result.reason == "answer_complete"
    assert any(
        msg["role"] == "user" and "Ordering hint" in msg["content"]
        for msg in client.calls[1]
    )


@pytest.mark.asyncio()
async def test_react_planner_parallel_plan_executes_concurrently() -> None:
    client = StubClient(
        [
            {
                "thought": "fan out",
                "plan": [
                    {
                        "node": "fetch_primary",
                        "args": {"topic": "topic", "shard": 0},
                    },
                    {
                        "node": "fetch_secondary",
                        "args": {"topic": "topic", "shard": 1},
                    },
                ],
                "join": {"node": "merge_results"},
            },
            {
                "thought": "finish",
                "next_node": None,
                "args": {"answer": "done"},
            },
        ]
    )

    registry = ModelRegistry()
    registry.register("fetch_primary", ShardRequest, ShardPayload)
    registry.register("fetch_secondary", ShardRequest, ShardPayload)
    registry.register("merge_results", MergeArgs, Documents)

    nodes = [
        Node(fetch_primary, name="fetch_primary"),
        Node(fetch_secondary, name="fetch_secondary"),
        Node(merge_results, name="merge_results"),
    ]

    planner = ReactPlanner(
        llm_client=client,
        catalog=build_catalog(nodes, registry),
    )

    start = time.perf_counter()
    result = await planner.run("parallel fan out")
    elapsed = time.perf_counter() - start

    assert elapsed < 0.1
    assert result.reason == "answer_complete"

    step = result.metadata["steps"][0]
    assert step["action"]["plan"]
    join_obs = step["observation"]["join"]["observation"]
    assert join_obs["documents"] == ["topic-primary", "topic-secondary"]
    assert step["observation"]["stats"] == {"success": 2, "failed": 0}


@pytest.mark.asyncio()
async def test_react_planner_parallel_plan_handles_branch_failure() -> None:
    AUDIT_CALLS.clear()
    client = StubClient(
        [
            {
                "thought": "fan out",
                "plan": [
                    {"node": "retrieve", "args": {"intent": "docs"}},
                    {"node": "broken", "args": {"intent": "docs"}},
                ],
                "join": {"node": "audit_parallel"},
            },
            {
                "thought": "finish",
                "next_node": None,
                "args": {"answer": "done"},
            },
        ]
    )

    registry = ModelRegistry()
    registry.register("retrieve", Intent, Documents)
    registry.register("broken", Intent, Documents)
    registry.register("audit_parallel", AuditArgs, Documents)

    nodes = [
        Node(retrieve, name="retrieve"),
        Node(broken, name="broken"),
        Node(audit_parallel, name="audit_parallel"),
    ]

    planner = ReactPlanner(
        llm_client=client,
        catalog=build_catalog(nodes, registry),
    )

    result = await planner.run("parallel failure")

    assert result.reason == "answer_complete"
    step = result.metadata["steps"][0]
    branches = step["observation"]["branches"]
    failures = [entry for entry in branches if "error" in entry]
    assert len(failures) == 1
    assert "did not validate" in failures[0]["error"]

    join_info = step["observation"]["join"]
    assert join_info["status"] == "skipped"
    assert join_info["reason"] == "branch_failures"
    assert join_info["failures"][0]["node"] == "broken"
    assert AUDIT_CALLS == []


@pytest.mark.asyncio()
async def test_react_planner_parallel_plan_rejects_invalid_node() -> None:
    client = StubClient(
        [
            {
                "thought": "invalid",
                "plan": [{"node": "missing", "args": {}}],
            },
            {
                "thought": "finish",
                "next_node": None,
                "args": {"answer": "done"},
            },
        ]
    )

    registry = ModelRegistry()
    registry.register("respond", Answer, Answer)
    nodes = [Node(respond, name="respond")]

    planner = ReactPlanner(
        llm_client=client,
        catalog=build_catalog(nodes, registry),
    )

    result = await planner.run("invalid parallel plan")

    first_step = result.metadata["steps"][0]
    assert "Parallel plan invalid" in first_step["error"]


@pytest.mark.asyncio()
async def test_react_planner_deadline_enforcement() -> None:
    """Planner should respect deadline_s and return budget_exhausted."""
    # Provide enough responses so stub doesn't run out
    client = StubClient(
        [
            {
                "thought": "step1",
                "next_node": "triage",
                "args": {"question": "step1"},
            },
            {
                "thought": "step2",
                "next_node": "triage",
                "args": {"question": "step2"},
            },
            {
                "thought": "step3",
                "next_node": "triage",
                "args": {"question": "step3"},
            },
        ]
    )
    registry = ModelRegistry()
    registry.register("triage", Query, Intent)

    # Use custom time source to control deadline precisely
    start_time = time.monotonic()

    def controlled_time() -> float:
        # After first call, advance past deadline
        if hasattr(controlled_time, "calls"):
            controlled_time.calls += 1
            if controlled_time.calls > 5:  # After a few calls, trigger deadline
                return start_time + 10.0  # Way past 0.01s deadline
        else:
            controlled_time.calls = 0
        return start_time

    planner = ReactPlanner(
        llm_client=client,
        catalog=build_catalog([Node(triage, name="triage")], registry),
        deadline_s=0.01,  # 10ms deadline
        max_iters=10,
        time_source=controlled_time,
    )

    result = await planner.run("Test deadline")

    assert result.reason == "budget_exhausted"
    assert result.metadata["constraints"]["deadline_triggered"] is True


@pytest.mark.asyncio()
async def test_react_planner_absolute_max_parallel_enforced() -> None:
    """System-level max_parallel should prevent resource exhaustion."""
    # Try to request more than the absolute limit
    excessive_plan = [
        {"node": "respond", "args": {"answer": f"branch_{i}"}}
        for i in range(100)  # Way over default limit of 50
    ]

    client = StubClient(
        [
            {"thought": "excessive", "plan": excessive_plan},
            {
                "thought": "finish",
                "next_node": None,
                "args": {"answer": "done"},
            },
        ]
    )

    registry = ModelRegistry()
    registry.register("respond", Answer, Answer)
    nodes = [Node(respond, name="respond")]

    planner = ReactPlanner(
        llm_client=client,
        catalog=build_catalog(nodes, registry),
        absolute_max_parallel=50,
    )

    result = await planner.run("test absolute limit")

    # Should have error about parallel limit in the first step
    steps = result.metadata["steps"]
    assert len(steps) > 0
    first_step = steps[0]
    # The error should be present
    assert first_step.get("error") is not None
    assert "50" in first_step["error"]


@pytest.mark.asyncio()
async def test_react_planner_event_callback_receives_events() -> None:
    """Event callback should receive all planner events."""
    from penguiflow.planner import PlannerEvent

    events: list[PlannerEvent] = []

    def callback(event: PlannerEvent) -> None:
        events.append(event)

    client = StubClient(
        [
            {
                "thought": "triage",
                "next_node": "triage",
                "args": {"question": "Test"},
            },
            {"thought": "finish", "next_node": None, "args": {"answer": "done"}},
        ]
    )

    registry = ModelRegistry()
    registry.register("triage", Query, Intent)

    planner = ReactPlanner(
        llm_client=client,
        catalog=build_catalog([Node(triage, name="triage")], registry),
        event_callback=callback,
    )

    await planner.run("Test events")

    # Should have received events
    assert len(events) > 0

    event_types = {e.event_type for e in events}
    # Expect at least step_start, step_complete, finish
    assert "step_start" in event_types
    assert "step_complete" in event_types
    assert "finish" in event_types


@pytest.mark.asyncio()
async def test_react_planner_improved_token_estimation() -> None:
    """Token estimation should account for message structure overhead."""
    client = StubClient(
        [
            {"thought": "finish", "next_node": None, "args": {"answer": "done"}},
        ]
    )

    planner = make_planner(client)

    # Create messages and estimate tokens
    messages = [
        {"role": "system", "content": "a" * 100},
        {"role": "user", "content": "b" * 100},
        {"role": "assistant", "content": "c" * 100},
    ]

    tokens = planner._estimate_size(messages)

    # Should be approximately (300 chars + overhead) / 3.5
    # Overhead = 3 * (role length + 20) ≈ 3 * 30 = 90
    # Total ≈ 390 / 3.5 ≈ 111 tokens
    assert 100 < tokens < 130


@pytest.mark.asyncio()
async def test_react_planner_state_store_save_error_handled_gracefully() -> None:
    """State store save errors should not crash pause operation."""

    class FailingSaver:
        def save_planner_state(self, token: str, payload: dict) -> None:
            raise RuntimeError("Storage failed")

    client = StubClient(
        [
            {
                "thought": "approval",
                "next_node": "approval",
                "args": {"intent": "docs"},
            },
        ]
    )

    registry = ModelRegistry()
    registry.register("approval", Intent, Intent)
    nodes = [Node(approval_gate, name="approval")]

    planner = ReactPlanner(
        llm_client=client,
        catalog=build_catalog(nodes, registry),
        pause_enabled=True,
        state_store=FailingSaver(),
    )

    # Should still pause successfully despite state store failure
    result = await planner.run("Test state store error")
    assert isinstance(result, PlannerPause)
    assert result.resume_token is not None
