# app/main.py
from __future__ import annotations

from typing import Any, Dict, List
import uuid
import asyncio

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .engine import (
    NodeDef,
    EdgeDef,
    GraphDef,
    Run,
    RunStatus,
    GRAPHS,
    RUNS,
    execute_graph,
)
from .workflows_code_review import register_code_review_tools

app = FastAPI(title="Mini Agent Workflow Engine")

# Register built-in tools (code review workflow)
register_code_review_tools()


# ---------- API models ----------

class GraphCreateRequest(BaseModel):
    nodes: List[NodeDef]
    edges: List[EdgeDef]
    start_node: str


class GraphCreateResponse(BaseModel):
    graph_id: str


class GraphRunRequest(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any] = {}


class GraphRunResponse(BaseModel):
    run_id: str
    final_state: Dict[str, Any]
    status: RunStatus
    log: List[Dict[str, Any]]


class GraphRunStartResponse(BaseModel):
    """Used for async /graph/run_async"""
    run_id: str
    status: RunStatus


class RunStateResponse(BaseModel):
    run_id: str
    graph_id: str
    status: RunStatus
    current_node: str | None
    state: Dict[str, Any]
    log: List[Dict[str, Any]]
    error: str | None = None


# ---------- Endpoints ----------

@app.post("/graph/create", response_model=GraphCreateResponse)
async def create_graph(req: GraphCreateRequest) -> GraphCreateResponse:
    graph_id = str(uuid.uuid4())

    nodes_dict = {n.name: n for n in req.nodes}
    if req.start_node not in nodes_dict:
        raise HTTPException(status_code=400, detail="start_node must be one of the nodes")

    graph = GraphDef(
        id=graph_id,
        nodes=nodes_dict,
        edges=req.edges,
        start_node=req.start_node,
    )

    GRAPHS[graph_id] = graph
    return GraphCreateResponse(graph_id=graph_id)


@app.post("/graph/run", response_model=GraphRunResponse)
async def run_graph(req: GraphRunRequest) -> GraphRunResponse:
    """
    Synchronous execution: waits for the whole workflow to finish,
    then returns final_state + execution log.
    """
    graph = GRAPHS.get(req.graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")

    run_id = str(uuid.uuid4())
    run = Run(
        id=run_id,
        graph_id=graph.id,
        status=RunStatus.PENDING,
        state=req.initial_state.copy(),
        log=[],
    )
    RUNS[run_id] = run

    # Run in the current request
    await execute_graph(graph, run)

    return GraphRunResponse(
        run_id=run_id,
        final_state=run.state,
        status=run.status,
        log=[entry.dict() for entry in run.log],
    )


@app.post("/graph/run_async", response_model=GraphRunStartResponse)
async def run_graph_async(req: GraphRunRequest, background_tasks: BackgroundTasks) -> GraphRunStartResponse:
    """
    Asynchronous execution: starts the workflow in a background task
    and immediately returns run_id + initial status.
    Client can poll /graph/state/{run_id} or use WebSocket.
    """
    graph = GRAPHS.get(req.graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")

    run_id = str(uuid.uuid4())
    run = Run(
        id=run_id,
        graph_id=graph.id,
        status=RunStatus.PENDING,
        state=req.initial_state.copy(),
        log=[],
    )
    RUNS[run_id] = run

    # schedule background execution
    background_tasks.add_task(execute_graph, graph, run)

    return GraphRunStartResponse(
        run_id=run_id,
        status=run.status,
    )


@app.get("/graph/state/{run_id}", response_model=RunStateResponse)
async def get_run_state(run_id: str) -> RunStateResponse:
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return RunStateResponse(
        run_id=run.id,
        graph_id=run.graph_id,
        status=run.status,
        current_node=run.current_node,
        state=run.state,
        log=[entry.dict() for entry in run.log],
        error=run.error,
    )


# ---------- WebSocket: live log streaming ----------

@app.websocket("/ws/run/{run_id}")
async def websocket_run_logs(websocket: WebSocket, run_id: str):
    """
    Streams execution logs for a given run_id.
    Sends new log entries as they appear, until the run completes or fails.
    """
    await websocket.accept()

    if run_id not in RUNS:
        await websocket.send_json({"error": "Run not found"})
        await websocket.close()
        return

    last_index = 0

    try:
        while True:
            run = RUNS.get(run_id)
            if not run:
                await websocket.send_json({"error": "Run not found"})
                break

            # Send any new log entries
            if len(run.log) > last_index:
                new_entries = run.log[last_index:]
                for entry in new_entries:
                    await websocket.send_json({
                        "node": entry.node,
                        "state_snapshot": entry.state_snapshot,
                        "status": run.status,
                    })
                last_index = len(run.log)

            # If finished and nothing more to send, close
            if run.status in (RunStatus.COMPLETED, RunStatus.FAILED) and len(run.log) == last_index:
                await websocket.send_json({"status": run.status, "done": True})
                break

            await asyncio.sleep(0.3)
    except WebSocketDisconnect:
        # client disconnected, just stop
        return
    finally:
        await websocket.close()


# ---------- Convenience: sample graph definition for Code Review workflow ----------

@app.post("/graph/create_sample/code_review", response_model=GraphCreateResponse)
async def create_sample_code_review_graph() -> GraphCreateResponse:
    """
    Creates a sample Code Review Mini-Agent workflow:

      extract_functions -> check_complexity -> detect_basic_issues
      -> suggest_improvements -> evaluate_quality

    Loop:
      If state['quality_ok'] == False after evaluate_quality,
      we go back to extract_functions. Otherwise, stop.
    """
    graph_id = str(uuid.uuid4())

    nodes = [
        NodeDef(name="extract_functions", tool="extract_functions"),
        NodeDef(name="check_complexity", tool="check_complexity"),
        NodeDef(name="detect_basic_issues", tool="detect_basic_issues"),
        NodeDef(name="suggest_improvements", tool="suggest_improvements"),
        NodeDef(name="evaluate_quality", tool="evaluate_quality"),
    ]

    edges = [
        EdgeDef(from_node="extract_functions", to_node="check_complexity"),
        EdgeDef(from_node="check_complexity", to_node="detect_basic_issues"),
        EdgeDef(from_node="detect_basic_issues", to_node="suggest_improvements"),
        EdgeDef(from_node="suggest_improvements", to_node="evaluate_quality"),
        # loop edge: if quality_ok is False, go back to extract_functions
        EdgeDef(
            from_node="evaluate_quality",
            to_node="extract_functions",
            condition_key="quality_ok",
            operator="eq",
            value=False,
        ),
        # no edge when quality_ok == True -> workflow terminates
    ]

    graph = GraphDef(
        id=graph_id,
        nodes={n.name: n for n in nodes},
        edges=edges,
        start_node="extract_functions",
    )

    GRAPHS[graph_id] = graph
    return GraphCreateResponse(graph_id=graph_id)
