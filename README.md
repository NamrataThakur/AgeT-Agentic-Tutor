
# AgeT

**AgeT (Agentic Technical Interviewer)** is an AI-powered, agentic technical interviewing system designed to conduct adaptive, knowledge-grounded technical interviews. It is an adaptive, multi-turn, graph-native, RAG-grounded, stateful interview system with planner-evaluator separation and topic-switch aware execution.

AgeT combines **LLMs, LangGraph-based agent orchestration, GraphRAG, semantic retrieval, structured question banks, memory, and MCP-based capabilities** to create interviews that are context-aware, adaptive, and technically consistent.

### Key Capabilities

* **Agentic Interview Orchestration** — Coordinates specialized agents through a LangGraph-based workflow for planning, questioning, evaluation, and interview progression.
* **Knowledge-Grounded Interviews** — Builds a structured knowledge base from technical sources using semantic chunking, embeddings, GraphRAG, and hybrid retrieval.
* **Intelligent Question Bank Generation** — Generates structured question banks from the underlying knowledge base, including question difficulty and primary/secondary concepts.
* **Adaptive Question Selection** — Selects questions based on the current interview context, previously asked questions, difficulty, and relevant concepts.
* **Question Evaluation** — Evaluates candidate responses against the expected technical concepts and context.
* **Memory & Context Management** — Maintains conversation history and active interview context through session-based memory.
* **Knowledge Maintenance** — Monitors question-bank buckets for health and supports targeted regeneration when required.
* **MCP-Based Knowledge Capabilities** — Exposes knowledge operations through a Knowledge MCP layer so that interview runtime and maintenance workflows can consume shared knowledge capabilities through well-defined tools.
* **Asynchronous Knowledge Operations** — Supports long-running operations such as question-bank generation through background execution, allowing the interview workflow to pause and resume without blocking the request.
* **Execution Guardrails** — Designed to support execution limits, tool authorization, timeouts, context/token budgets, state-transition controls, and observability.
* **Extensible Architecture** — Separates agents, orchestration, application services, knowledge services, memory, MCP capabilities, and infrastructure so additional capabilities can be introduced without tightly coupling the system.

### Architecture at a Glance

```text
                         AgeT
                           │
             ┌─────────────┴─────────────┐
             │                           │
        Interview Runtime          Knowledge & Maintenance
             │                           │
             ▼                           ▼
        LangGraph                    MCP Client
             │                           │
       Specialized Agents               ▼
             │                     Knowledge MCP
             │                           │
             └─────────────┬─────────────┘
                           ▼
                  Knowledge Services
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
         GraphRAG      Question Bank   Maintenance
         Retrieval     Generation       & Regeneration
```

AgeT is being developed with a focus on **modularity, reliable agent execution, knowledge grounding, extensibility, and clear separation between agent reasoning and deterministic system capabilities**.

