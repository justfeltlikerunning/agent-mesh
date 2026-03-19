<p align="center">
  <img src="assets/banner.png" alt="MESH Banner" width="100%">
</p>

# 🐝 MESH: Message Envelope for Structured Handoffs

**Reliable inter-agent messaging for any AI agent framework.**

MESH adds structured communication between AI agents running on separate hosts. It uses simple HTTP webhooks with no external message bus required — just bash, curl, and jq.

**Works with:** [OpenClaw](https://github.com/openclaw/openclaw) · [CrewAI](https://github.com/crewai-inc/crewai) · [LangGraph](https://github.com/langchain-ai/langgraph) · [AutoGen](https://github.com/microsoft/autogen) · [LlamaIndex](https://github.com/run-llama/llama_index) · Any HTTP-capable agent

**Current version: v3.2**

## Who Is This For?

**You're running more than one AI agent** and they need to coordinate. Maybe they're on:

- 🖥️ Separate VMs on a LAN
- 🐳 Docker containers on a shared network
- ☁️ Cloud instances across regions
- 🏠 A mix of all of the above

If you just have one agent on one computer, you don't need this. MESH is for when your agents live on different hosts and need to talk to each other, send requests, share results, coordinate work, and not lose messages when something goes down.

**What it's NOT:** This isn't a replacement for your framework's built-in tool calling or memory. MESH is the *backchannel* — agent-to-agent communication across hosts.

## What Can Agents Do With MESH?

- **Cross-check data:** Two agents independently query the same metric and compare results
- **Collaborative discovery:** Agents brainstorm on data, one finds a pattern, the other validates it, they generate follow-up questions humans didn't think to ask
- **Escalation chains:** A monitoring agent detects an issue, asks a domain expert to investigate, expert shares findings, hub-node decides action
- **Fleet-wide broadcasts:** Push a config change or correction to all agents at once
- **Consensus gathering:** Ask all agents for their opinion on a topic, collect responses, set a verdict
- **Self-healing:** Agent detects a problem, fixes it, notifies the fleet it's back

## Quick Start

### Install

```bash
git clone https://github.com/justfeltlikerunning/agent-mesh.git
cd agent-mesh
bash install.sh --agent myagent
```

This creates the MESH directory structure with scripts, config, and state files. Add to your `.bashrc`:

```bash
export MESH_HOME="$HOME/agent-mesh"
export MESH_AGENT="myagent"
export PATH="$MESH_HOME/bin:$PATH"
```

### Configure Agents

Edit `config/agent-registry.json`:

```json
{
  "version": "2.0",
  "agents": {
    "researcher": {
      "ip": "10.0.0.10",
      "port": 8900,
      "token": "researcher-token",
      "role": "research",
      "hookPath": "/mesh/inbox"
    },
    "analyst": {
      "ip": "10.0.0.11",
      "port": 8900,
      "token": "analyst-token",
      "role": "analysis",
      "hookPath": "/mesh/inbox"
    }
  }
}
```

### Send Messages

```bash
# Send a request (expects a response)
mesh-send.sh analyst request "What's the current database status?"

# Send a notification (fire-and-forget)
mesh-send.sh analyst notification "Schema updated, please refresh"

# Broadcast to all agents
mesh-send.sh all notification "Fleet-wide maintenance window starting"

# Rally multiple agents (fan-out request)
mesh-rally.sh "Status report please" --agents "researcher,analyst"
```

### Receive Messages

MESH includes a standalone Python receiver that works with any framework:

```bash
# Start the receiver on any host
MESH_AGENT=analyst python3 receivers/generic-receiver.py --port 8900
```

Your agent framework polls for messages:

```python
import requests

# Poll inbox
messages = requests.get("http://localhost:8900/inbox").json()["messages"]
for msg in messages:
    task = msg["payload"]["body"]
    sender = msg["from"]
    # Feed to your agent framework...
```

Or use handler mode for auto-processing:

```bash
MESH_HANDLER=./my-handler.sh MESH_AGENT=analyst python3 receivers/generic-receiver.py
```

## Framework Integration

### OpenClaw

MESH was originally built for OpenClaw and integrates natively with its webhook system:

```bash
bash install.sh --agent myagent --openclaw
# Configures hookPath to /hooks/<agent>, reads openclaw.json for port/token
```

### CrewAI

Use MESH to coordinate CrewAI Crews running on different hosts:

```python
# integrations/crewai_example.py
import requests
from crewai import Agent, Task, Crew

# Define a tool that sends MESH messages
def send_to_remote_agent(agent_name: str, message: str) -> str:
    """Send a message to a remote agent via MESH and get the response."""
    resp = requests.post("http://localhost:8900/send", json={
        "to": agent_name,
        "type": "request",
        "payload": {"body": message}
    })
    return resp.json().get("response", "No response yet")

# CrewAI agent with MESH tool
researcher = Agent(
    role="Researcher",
    goal="Research topics and coordinate with remote analysts",
    tools=[send_to_remote_agent]
)

# The remote analyst runs on a different host with its own MESH receiver
task = Task(
    description="Research this topic and ask the remote analyst to validate",
    agent=researcher
)

crew = Crew(agents=[researcher], tasks=[task])
crew.kickoff()
```

### LangGraph

Integrate MESH as a node in your LangGraph state machine:

```python
# integrations/langgraph_example.py
import requests
from langgraph.graph import StateGraph, MessagesState, START, END

def mesh_send_node(state: MessagesState):
    """Send the last message to a remote agent via MESH."""
    last_msg = state["messages"][-1].content
    resp = requests.post("http://localhost:8900/send", json={
        "to": "remote-agent",
        "type": "request",
        "payload": {"body": last_msg}
    })
    result = resp.json()
    return {"messages": [{"role": "assistant", "content": result.get("response", "Sent")}]}

def mesh_poll_node(state: MessagesState):
    """Poll for responses from remote agents."""
    messages = requests.get("http://localhost:8900/inbox").json()["messages"]
    if messages:
        return {"messages": [{"role": "assistant", "content": m["payload"]["body"]} for m in messages]}
    return state

graph = StateGraph(MessagesState)
graph.add_node("send_remote", mesh_send_node)
graph.add_node("poll_response", mesh_poll_node)
graph.add_edge(START, "send_remote")
graph.add_edge("send_remote", "poll_response")
graph.add_edge("poll_response", END)
app = graph.compile()
```

### AutoGen (Microsoft)

Use MESH with AutoGen's event-driven Core layer:

```python
# integrations/autogen_example.py
import requests
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

# MESH tool for AutoGen agents
async def mesh_request(agent_name: str, question: str) -> str:
    """Send a request to a remote agent via MESH protocol."""
    resp = requests.post("http://localhost:8900/send", json={
        "to": agent_name,
        "type": "request",
        "payload": {"body": question}
    })
    return resp.json().get("response", "Message sent, awaiting response")

agent = AssistantAgent(
    "hub-node",
    model_client=OpenAIChatCompletionClient(model="gpt-4o"),
    tools=[mesh_request],
    system_message="You coordinate with remote agents using the mesh_request tool."
)
```

### LlamaIndex

Wire MESH into LlamaIndex's AgentWorkflow for cross-host hand-offs:

```python
# integrations/llamaindex_example.py
import requests
from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent
from llama_index.core.tools import FunctionTool

def mesh_handoff(agent_name: str, task: str) -> str:
    """Hand off a task to a remote agent via MESH."""
    resp = requests.post("http://localhost:8900/send", json={
        "to": agent_name,
        "type": "request",
        "payload": {"body": task}
    })
    return resp.json().get("response", "Task handed off")

mesh_tool = FunctionTool.from_defaults(fn=mesh_handoff)

local_agent = FunctionAgent(
    name="Hub-Node",
    description="Coordinates work and hands off to remote specialists",
    tools=[mesh_tool]
)

workflow = AgentWorkflow(agents=[local_agent], root_agent="Hub-Node")
```

### Generic HTTP (Any Framework)

MESH is just HTTP + JSON. Any agent that can make HTTP requests can use it:

```bash
# Send a message via the REST API
curl -X POST http://localhost:8900/send \
  -H "Content-Type: application/json" \
  -d '{"to":"remote-agent","type":"request","payload":{"body":"Hello from any framework"}}'

# Poll for responses
curl http://localhost:8900/inbox
```

## Features

### Core Messaging (v1.0)

| Feature | Description |
|---------|-------------|
| Structured envelopes | Every message has sender, recipient, type, correlation ID, timestamps |
| Retry with backoff | 4 attempts with exponential backoff (2s, 4s, 8s) |
| Circuit breakers | Auto-open after 3 failures, 60s cooldown, half-open probe |
| Dead letter queue | Failed messages saved and auto-replayed when agent recovers |
| Alert deduplication | Groups alerts by host and check type, suppresses duplicates |
| Audit logging | Every message logged to `logs/mesh-audit.jsonl` |
| Rich attachments | Files (auto base64 if under 64KB) and URL references |
| Broadcast and rally | Fan-out to all, groups, or selected agents |

### Mesh Resilience (v2.0)

| Feature | Description |
|---------|-------------|
| Peer discovery | Continuous health probing with latency tracking |
| Relay failover | Hub goes down? Another agent auto-promotes |
| Persistent message queue | Store-and-forward with auto-replay |
| Envelope encryption | AES-256-CBC for sensitive payloads |
| HMAC signing | Per-agent cryptographic message authentication |
| TTL enforcement | Expired messages auto-purge and are rejected on receive |
| Replay protection | Nonce and timestamp prevents message replay attacks |
| Collaborative sessions | Persistent multi-agent conversations with shared context |

### Conversation Threading (v3.0+)

| Feature | Description |
|---------|-------------|
| Conversations | Group related messages under a shared conversation ID |
| Multi-round rallies | Ask a question, collect responses, ask follow-up, repeat |
| Consensus | Agents discuss, then a verdict is set via CLI or API |
| Conversation types | Rally, collab, escalation, broadcast, opinion, brainstorm |
| Auto-timeout | Stale conversations auto-close after configurable duration |
| Dashboard | Visual threaded view with real-time SSE updates |

## Architecture

```
┌──────────┐    MESH envelope     ┌──────────┐
│  Agent A  │ ──────────────────> │  Agent B  │
│ (any      │    HTTP POST        │ (any      │
│ framework)│                     │ framework)│
│           │ <────────────────── │           │
│           │    MESH response    │           │
└──────────┘                      └──────────┘

Envelope:
{
  "protocol": "mesh/3.0",
  "id": "msg_<uuid>",
  "conversationId": "conv_<id>",
  "from": "agentA",
  "to": "agentB",
  "type": "request|notification|response|broadcast",
  "timestamp": "ISO-8601",
  "payload": { "subject": "...", "body": "..." },
  "signature": "<hmac-sha256>"
}
```

## Security

| Layer | Default | Description |
|-------|---------|-------------|
| Bearer tokens | Yes | Every HTTP request includes authorization header |
| HMAC signing | Opt-in | SHA256 signature on full envelope |
| Envelope encryption | Opt-in | AES-256-CBC for sensitive payloads |
| TTL + Replay protection | Opt-in | Timestamp + nonce rejects replayed messages |

## Requirements

| Package | Required |
|---------|----------|
| `bash` 4.0+ | Yes |
| `jq` | Yes |
| `curl` | Yes |
| `python3` | For receiver/conversations |
| `openssl` | For signing/encryption |

No Node.js, no Python frameworks, no compiled binaries. Pure bash + jq + curl.

## License

MIT

## Related Projects

- **[openclaw-mesh](https://github.com/justfeltlikerunning/openclaw-mesh)** — The OpenClaw-native version with deeper webhook integration.
- **[agent-pulse](https://github.com/justfeltlikerunning/agent-pulse)** — Real-time WebSocket hub for sub-millisecond agent communication.
- **[openclaw-pulse](https://github.com/justfeltlikerunning/openclaw-pulse)** — OpenClaw-native version of agent-pulse.
- **[PulseNet](https://github.com/justfeltlikerunning/pulsenet)** — Multi-agent chat interface with pipeline dispatch.
- **[OpenClaw](https://github.com/openclaw/openclaw)** — AI agent runtime.
