"""
MESH + LlamaIndex Integration Example

Uses MESH for cross-host agent hand-offs in LlamaIndex AgentWorkflow.
The hub-node agent can hand off tasks to remote specialists.
"""
import requests
from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent
from llama_index.core.tools import FunctionTool

MESH_API = "http://localhost:8900"

def mesh_handoff(agent_name: str, task_description: str) -> str:
    """Hand off a task to a remote specialist agent via MESH."""
    resp = requests.post(f"{MESH_API}/send", json={
        "to": agent_name,
        "type": "request",
        "payload": {"subject": "Task handoff", "body": task_description}
    })
    return f"Task handed off to {agent_name}: {resp.json()}"

def mesh_check_results() -> str:
    """Check for completed results from remote agents."""
    messages = requests.get(f"{MESH_API}/inbox").json().get("messages", [])
    if messages:
        return "\n".join(f"{m['from']}: {m['payload']['body']}" for m in messages)
    return "No results yet"

handoff_tool = FunctionTool.from_defaults(fn=mesh_handoff)
results_tool = FunctionTool.from_defaults(fn=mesh_check_results)

hub-node = FunctionAgent(
    name="Hub-Node",
    description="Coordinates tasks across remote specialist agents",
    system_prompt=(
        "You manage a team of remote specialist agents. "
        "Use mesh_handoff to send tasks to specialists and "
        "mesh_check_results to collect their work."
    ),
    tools=[handoff_tool, results_tool]
)

workflow = AgentWorkflow(agents=[hub-node], root_agent="Hub-Node")

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(workflow.run("Analyze Q1 performance and have the analyst validate"))
    print(result)
