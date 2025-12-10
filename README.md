# Mini Agent Workflow Engine – Backend Assignment

This project implements a minimal workflow and graph execution engine using Python and FastAPI. It was developed as part of an AI Engineering Internship assignment to demonstrate backend design, workflow orchestration, async execution, and clean code structure. The system allows defining nodes as Python functions, connecting them using edges, maintaining a shared state, and executing workflows end-to-end through REST APIs and WebSockets.
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Key Features

Workflow Engine  
- Nodes implemented as Python functions (tools)  
- Shared mutable dictionary-based state  
- Directed edges between nodes  
- Conditional branching based on state values  
- State-driven looping until a condition is satisfied  
- Step-by-step execution logs for every run  

Tool Registry  
- Tools registered dynamically  
- Nodes invoke tools during execution  
- Supports both sync and async functions  

FastAPI APIs  
- POST /graph/create – Create a workflow  
- POST /graph/run – Execute workflow synchronously  
- POST /graph/run_async – Execute workflow in background  
- GET /graph/state/{run_id} – Fetch current workflow state  
- WebSocket /ws/run/{run_id} – Stream live execution logs  
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Example Workflow Included – Code Review Mini-Agent

Workflow Steps  
1. Extract functions from code  
2. Check complexity  
3. Detect basic issues  
4. Suggest improvements  
5. Loop until quality_score >= threshold  

This workflow is fully rule-based and does not use any machine learning.
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Project Structure

mini-workflow-engine/  
│  
├── app/  
│   ├── __init__.py  
│   ├── main.py                  (FastAPI application entry point)  
│   ├── engine.py                (Workflow engine and execution logic)  
│   └── workflows_code_review.py (Example Code Review workflow)  
│  
├── requirements.txt  
├── .gitignore  
└── README.md  

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Installation

Step 1: Create a virtual environment  
python -m venv venv  

Step 2: Activate the virtual environment  

For Windows  
venv\Scripts\activate  

For Mac/Linux  
source venv/bin/activate  

Step 3: Install dependencies  
pip install -r requirements.txt  
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Run the Application

Start the FastAPI server using:  
uvicorn app.main:app --reload  

Open API documentation in your browser at:  
http://127.0.0.1:8000/docs  

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Sample Workflow Execution Input

```json
{
  "graph_id": "YOUR_GRAPH_ID",
  "initial_state": {
    "code": "def foo():\n    print('hi')\n    # TODO improve",
    "quality_threshold": 7
  }
}
