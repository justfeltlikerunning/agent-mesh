"""
MESH + AutoGen Integration Example

Uses MESH as a tool for AutoGen agents to communicate with remote agents
running on different hosts, regardless of what framework those agents use.
"""
import asyncio
import requests
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

MESH_API = "http://localhost:8900"

async def mesh_request(agent_name: str, question: str) -> str:
    """Send a request to a remote agent via MESH protocol."""
    resp = requests.post(f"{MESH_API}/send", json={
        "to": agent_name,
        "type": "request",
        "payload": {"subject": "AutoGen query", "body": question}
    })
    return str(resp.json())

async def mesh_poll() -> str:
    """Poll for incoming MESH messages."""
    messages = requests.get(f"{MESH_API}/inbox").json().get("messages", [])
    if messages:
        return "\n".join(f"From {m['from']}: {m['payload']['body']}" for m in messages)
    return "No new messages"

async def main():
    agent = AssistantAgent(
        "coordinator",
        model_client=OpenAIChatCompletionClient(model="gpt-4o"),
        tools=[mesh_request, mesh_poll],
        system_message=(
            "You coordinate work across a fleet of remote agents. "
            "Use mesh_request to send tasks to remote agents and "
            "mesh_poll to check for responses."
        )
    )
    result = await agent.run(task="Ask the 'analyst' agent for a status report")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
