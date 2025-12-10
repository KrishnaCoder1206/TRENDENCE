from __future__ import annotations

from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Literal
import asyncio
from pydantic import BaseModel

# ------------ Tool registry ------------

ToolFunc = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolFunc] = {}

    def register(self, name: str, func: Callable[[Dict[str, Any]], Any]) -> None:
        """
        Register a sync or async function as a tool.
        """
        if asyncio.iscoroutinefunction(func):
            async_func = func  # type: ignore[assignment]
        else:
            async def async_func(state: Dict[str, Any]) -> Dict[str, Any]:
                return func(state)  # type: ignore[call-arg]

        self._tools[name] = async_func  # type: ignore[assignment]

    def get(self, name: str) -> ToolFunc:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered")
        return self._tools[name]


tool_registry = ToolRegistry()


# ------------ Graph models ------------

class NodeDef(BaseModel):
    name: str
    tool: str  # tool name registered in ToolRegistry


class EdgeDef(BaseModel):
    from_node: str
    to_node: str
    condition_key: Optional[str] = None
    operator: Literal["eq", "ne", "lt", "gt", "lte", "gte"] = "eq"
    value: Optional[Any] = None


class GraphDef(BaseModel):
    id: str
    nodes: Dict[str, NodeDef]
    edges: List[EdgeDef]
    start_node: str


class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RunLogEntry(BaseModel):
    node: str
    state_snapshot: Dict[str, Any]


class Run(BaseModel):
    id: str
    graph_id: str
    status: RunStatus = RunStatus.PENDING
    current_node: Optional[str] = None
    state: Dict[str, Any] = {}
    log: List[RunLogEntry] = []
    error: Optional[str] = None


# ------------ In-memory stores ------------

GRAPHS: Dict[str, GraphDef] = {}
RUNS: Dict[str, Run] = {}


# ------------ Engine logic ------------

def _compare(a: Any, op: str, b: Any) -> bool:
    if op == "eq":
        return a == b
    if op == "ne":
        return a != b
    if op == "lt":
        return a < b
    if op == "gt":
        return a > b
    if op == "lte":
        return a <= b
    if op == "gte":
        return a >= b
    raise ValueError(f"Unsupported operator: {op}")


def _next_node_name(graph: GraphDef, node_name: str, state: Dict[str, Any]) -> Optional[str]:
    candidates = [e for e in graph.edges if e.from_node == node_name]

    for edge in candidates:
        if edge.condition_key is None:
            # unconditional edge
            return edge.to_node

        value_in_state = state.get(edge.condition_key)
        if _compare(value_in_state, edge.operator, edge.value):
            return edge.to_node

    # no matching edge => terminate
    return None


async def execute_graph(graph: GraphDef, run: Run) -> None:
    run.status = RunStatus.RUNNING
    node_name: Optional[str] = graph.start_node

    try:
        while node_name is not None:
            run.current_node = node_name
            node = graph.nodes[node_name]
            tool = tool_registry.get(node.tool)

            # call node tool
            run.state = await tool(run.state)

            # append to log (snapshot)
            run.log.append(RunLogEntry(node=node_name, state_snapshot=run.state.copy()))

            # compute next node (supports branching + loops)
            node_name = _next_node_name(graph, node_name, run.state)

        run.current_node = None
        run.status = RunStatus.COMPLETED
    except Exception as exc:
        run.status = RunStatus.FAILED
        run.error = str(exc)
