# Graph Report - personal-assistance  (2026-10-26)

## Corpus Check
- Corpus is ~6,959 words - fits in a single context window. You may not need a graph.

## Summary
- 177 nodes · 245 edges · 12 communities (5 shown, 7 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 16 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- External Dependencies & Messaging
- CLI Chat Interface
- Database Storage & Operations
- Architecture Design & Specifications
- LLM Note Processor Agent
- LangGraph Workflow Orchestration
- Docker & Database Infrastructure
- System Configuration & Prompts
- Architecture & Operational Docs
- Product Goals & Specifications

## God Nodes (most connected - your core abstractions)
1. `DatabaseAgent` - 20 edges
2. `ChatInterface` - 19 edges
3. `BaseAgent` - 15 edges
4. `NoteProcessorAgent` - 12 edges
5. `NoteProcessingWorkflow` - 12 edges
6. `db` - 6 edges
7. `main()` - 5 edges
8. `NoteProcessingWorkflow Orchestration` - 5 edges
9. `NoteProcessorAgent LLM Component` - 5 edges
10. `DatabaseAgent Storage Component` - 4 edges

## Surprising Connections (you probably didn't know these)
- `NoteProcessingWorkflow` --uses--> `DatabaseAgent`  [INFERRED]
  src/workflow.py → src/agents/database_agent.py
- `NoteProcessingWorkflow` --uses--> `NoteProcessorAgent`  [INFERRED]
  src/workflow.py → src/agents/note_processor.py
- `ChatInterface` --uses--> `NoteProcessingWorkflow`  [INFERRED]
  src/chat_interface.py → src/workflow.py
- `LangChain Execution Flow Requirement` --rationale_for--> `NoteProcessingWorkflow Orchestration`  [INFERRED]
  prompt.md → ARCHITECTURE.md
- `Personal Assistance Project Objectives` --semantically_similar_to--> `Project Specification Prompt`  [INFERRED] [semantically similar]
  README.md → prompt.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **End-to-End Note Processing Orchestration** — architecture_chat_interface, architecture_noteprocessingworkflow, architecture_noteprocessoragent, architecture_databaseagent [EXTRACTED 0.95]
- **PostgreSQL Storage and Setup Subsystem** — setup_postgres_docker, setup_data_definition, architecture_databaseagent, architecture_postgresql_schema [INFERRED 0.85]
- **Agent Polymorphic Extensibility Hierarchy** — architecture_baseagent, architecture_noteprocessoragent, architecture_databaseagent [EXTRACTED 0.95]

## Communities (12 total, 7 thin omitted)

### Community 3 - "Architecture Design & Specifications"
Cohesion: 0.14
Nodes (11): ChatInterface Component, Note Classification Taxonomy, DatabaseAgent Storage Component, NoteProcessingWorkflow Orchestration, NoteProcessorAgent LLM Component, PostgreSQL Notes and Classifications Schema, WorkflowState Management, PostgreSQL DDL Initialization Script (+3 more)

### Community 6 - "Docker & Database Infrastructure"
Cohesion: 0.18
Nodes (10): container_name, environment, image, ports, volumes, POSTGRES_PASSWORD, services, db (+2 more)

### Community 7 - "System Configuration & Prompts"
Cohesion: 0.18
Nodes (4): get_chat_config(), get_database_config(), get_llm_config(), get_system_prompt()

### Community 9 - "Architecture & Operational Docs"
Cohesion: 0.50
Nodes (3): Personal Assistance System Architecture, System Python Dependencies Specification, Personal Assistance Usage Documentation

### Community 10 - "Product Goals & Specifications"
Cohesion: 0.50
Nodes (4): Project Specification Prompt, Intelligent ANKI Flashcards Objective, Personal Assistance Project Objectives, Elasticsearch and Vector Embedding Search Objective

## Knowledge Gaps
- **11 isolated node(s):** `WorkflowState Management`, `Note Classification Taxonomy`, `Intelligent ANKI Flashcards Objective`, `Elasticsearch and Vector Embedding Search Objective`, `Personal Assistance Usage Documentation` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 96 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DatabaseAgent` connect `Database Storage & Operations` to `External Dependencies & Messaging`, `Agent Lifecycle Management`, `LangGraph Workflow Orchestration`?**
  _High betweenness centrality (0.246) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `NoteProcessingWorkflow` (e.g. with `ChatInterface` and `DatabaseAgent`) actually correct?**
  _`NoteProcessingWorkflow` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `WorkflowState Management`, `Note Classification Taxonomy`, `Intelligent ANKI Flashcards Objective` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `External Dependencies & Messaging` be split into smaller, more focused modules?**
  _Cohesion score 0.08235294117647059 - nodes in this community are weakly interconnected._
- **Why does `ChatInterface` connect `CLI Chat Interface` to `External Dependencies & Messaging`, `LangGraph Workflow Orchestration`?**
  _High betweenness centrality (0.193) - this node is a cross-community bridge._
- **Should `CLI Chat Interface` be split into smaller, more focused modules?**
  _Cohesion score 0.08912655971479501 - nodes in this community are weakly interconnected._
- **Why does `NoteProcessingWorkflow` connect `LangGraph Workflow Orchestration` to `External Dependencies & Messaging`, `CLI Chat Interface`, `Database Storage & Operations`, `LLM Note Processor Agent`?**
  _High betweenness centrality (0.186) - this node is a cross-community bridge._