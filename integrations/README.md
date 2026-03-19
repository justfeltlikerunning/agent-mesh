# Framework Integration Examples

Each example shows how to use MESH with a popular AI agent framework.
All examples assume a MESH receiver is running locally:

```bash
MESH_AGENT=myagent python3 receivers/generic-receiver.py --port 8900
```

| File | Framework | Pattern |
|------|-----------|---------|
| `crewai_example.py` | CrewAI | MESH as a tool for Crew agents |
| `langgraph_example.py` | LangGraph | MESH send/receive as graph nodes |
| `autogen_example.py` | AutoGen | MESH as tools for AssistantAgent |
| `llamaindex_example.py` | LlamaIndex | MESH hand-offs in AgentWorkflow |

## Key Concept

MESH is framework-agnostic. Your agents can use **any** framework — or no framework at all.
The only requirement is HTTP: agents send and receive JSON over HTTP POST.

A CrewAI agent on Host A can coordinate with a LangGraph agent on Host B
through MESH without either knowing what framework the other uses.
