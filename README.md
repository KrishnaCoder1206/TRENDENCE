Mini Agent Workflow Engine – Backend Assignment

This project implements a minimal workflow and graph execution engine using Python and FastAPI.  
It was developed as part of an AI Engineering Internship assignment to demonstrate backend design, workflow orchestration, and clean code structure.

==================================================

Features

Workflow Engine
- Supports nodes (steps) connected through edges
- Shared state is passed between nodes
- Conditional branching based on state values
- Looping until a condition is satisfied
- Execution logs maintained for each run

Tool Registry
- Tools are simple Python functions
- Nodes can call tools during execution
- Tools are registered dynamically

FastAPI Endpoints
- POST /graph/create : Create a workflow
- POST /graph/run : Execute workflow (synchronous)
- POST /graph/run_async : Execute workflow in background
- GET /graph/state/{run_id} : Get current workflow state
- WebSocket /ws/run/{run_id} : Stream live execution logs

==================================================

Example Workflow Included: Code Review Mini-Agent

Workflow Steps:
1. Extract functions from code
2. Check complexity
3. Detect basic issues
4. Suggest improvements
5. Loop until quality_score >= threshold

This workflow is implemented using simple rule-based logic with no machine learning.

==================================================

Project Structure

mini-workflow-engine/  
│  
├── app/  
│   ├── __init__.py  
│   ├── main.py                  (FastAPI application entry point)  
│   ├── engine.py                (Workflow engine and execution logic)  
│   └── workflows_code_review.py (Example Code Review workflow)  
│  
├── .gitignore  
└── README.md  

==================================================

Installation

1. Create a virtual environment

python -m venv venv

2. Activate the virtual environment

For Windows:
venv\Scripts\activate

For Mac/Linux:
source venv/bin/activate

3. Install dependencies

pip install fastapi uvicorn pydantic

==================================================

Run the Application

Use the following command to start the FastAPI server:

uvicorn app.main:app --reload

Open API documentation in browser:

http://127.0.0.1:8000/docs

==================================================

Sample Workflow Execution Input

```json
{
  "graph_id": "YOUR_GRAPH_ID",
  "initial_state": {
    "code": "def foo():\n    print('hi')\n    # TODO improve",
    "quality_threshold": 7
  }
}
