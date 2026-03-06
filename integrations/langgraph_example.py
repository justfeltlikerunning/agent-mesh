"""
MESH + LangGraph Integration Example

Shows how to add MESH send/receive as nodes in a LangGraph state machine.
Remote agents coordinate through MESH while LangGraph manages the local flow.
"""
import requests
from langgraph.graph import StateGraph, MessagesState, START, END

MESH_API = "http://localhost:8900"

def analyze_locally(state: MessagesState):
    """Local analysis node — processes the user's request."""
    return {"messages": [{"role": "assistant", "content": "Local analysis complete. Sending to remote validator..."}]}

def send_to_remote(state: MessagesState):
    """Send findings to a remote agent via MESH for validation."""
    last_msg = state["messages"][-1].content if hasattr(state["messages"][-1], "content") else str(state["messages"][-1])
    resp = requests.post(f"{MESH_API}/send", json={
        "to": "validator",
        "type": "request",
        "payload": {"subject": "Validation needed", "body": last_msg}
    })
    return {"messages": [{"role": "assistant", "content": f"Sent to validator: {resp.json()}"}]}

def check_remote_response(state: MessagesState):
    """Poll for validation response from remote agent."""
    messages = requests.get(f"{MESH_API}/inbox").json().get("messages", [])
    if messages:
        body = messages[0]["payload"]["body"]
        return {"messages": [{"role": "assistant", "content": f"Validator says: {body}"}]}
    return {"messages": [{"role": "assistant", "content": "Awaiting validator response..."}]}

# Build the graph
graph = StateGraph(MessagesState)
graph.add_node("analyze", analyze_locally)
graph.add_node("send_remote", send_to_remote)
graph.add_node("check_response", check_remote_response)

graph.add_edge(START, "analyze")
graph.add_edge("analyze", "send_remote")
graph.add_edge("send_remote", "check_response")
graph.add_edge("check_response", END)

app = graph.compile()

if __name__ == "__main__":
    result = app.invoke({"messages": [{"role": "user", "content": "Analyze agent fleet performance"}]})
    print(result)
