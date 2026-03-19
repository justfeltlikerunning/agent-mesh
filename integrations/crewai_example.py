"""
MESH + CrewAI Integration Example

Run a MESH receiver on the same host as your CrewAI agents:
  MESH_AGENT=researcher python3 receivers/generic-receiver.py --port 8900

Then use this tool in your CrewAI agents to communicate with remote agents.
"""
import requests
from crewai import Agent, Task, Crew

MESH_API = "http://localhost:8900"

def send_mesh_request(agent_name: str, message: str) -> str:
    """Send a request to a remote agent via MESH and return the response."""
    resp = requests.post(f"{MESH_API}/send", json={
        "to": agent_name,
        "type": "request",
        "payload": {"subject": "CrewAI task", "body": message}
    })
    return resp.json().get("response", "Message sent, awaiting async response")

def poll_mesh_inbox() -> list:
    """Poll for incoming MESH messages."""
    return requests.get(f"{MESH_API}/inbox").json().get("messages", [])

# Example: Researcher agent that coordinates with a remote analyst
researcher = Agent(
    role="Lead Researcher",
    goal="Research topics and validate findings with the remote analyst agent",
    backstory="You're a thorough researcher who always cross-validates with the analyst team.",
    tools=[send_mesh_request]
)

task = Task(
    description=(
        "Research the latest trends in multi-agent AI systems. "
        "Send your key findings to the 'analyst' agent for validation."
    ),
    agent=researcher,
    expected_output="A validated summary of multi-agent AI trends"
)

if __name__ == "__main__":
    crew = Crew(agents=[researcher], tasks=[task], verbose=True)
    result = crew.kickoff()
    print(result)
