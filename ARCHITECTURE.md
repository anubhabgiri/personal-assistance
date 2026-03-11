# Architecture & Design Documentation

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User (CLI)                               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              ChatInterface (chat_interface.py)              │
│  - Command parsing and routing                              │
│  - User interaction management                              │
│  - Result formatting and display                            │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│            NoteProcessingWorkflow (workflow.py)             │
│  LangGraph-based orchestration                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ State Graph: START → preprocess → process → store    │   │
│  │                                     → END            │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼────────┐  ┌────▼──────────┐  ┌─▼──────────────┐
│ Preprocessing  │  │ Processing    │  │ Storage        │
│ (Validation)   │  │ (LLM Agent)   │  │ (Database)     │
└────────────────┘  └────┬──────────┘  └────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
┌───────▼─────────────────┐   ┌──────────▼──────────────┐
│  NoteProcessorAgent     │   │  DatabaseAgent          │
│  (agents/)              │   │  (agents/)              │
│                         │   │                         │
│ - Load LLM model        │   │ - PostgreSQL conn       │
│ - Tokenization          │   │ - Store results         │
│ - Classification        │   │ - Query notes           │
│ - Summarization         │   │ - Search functions      │
│ - Tag generation        │   │                         │
└─────────────────────────┘   └─────────────────────────┘
         │                              │
         │                              │
    Transformer                  PostgreSQL
    Model (GPU)                   Database
```

## Component Details

### 1. ChatInterface (`src/chat_interface.py`)

**Responsibility**: User interaction and command handling

**Key Methods**:
- `run()`: Main event loop
- `process_note_interactive()`: Handle note input
- `database_operations()`: Menu for DB operations
- `print_welcome()`: Display welcome screen

**Commands**:
```
/process     → Collect and process note
/model       → Load language model
/database    → Database operations (view, search)
/history     → Show session notes
/help        → Display commands
/exit        → Shutdown
```

### 2. NoteProcessingWorkflow (`src/workflow.py`)

**Responsibility**: Orchestrate agents using LangGraph

**Graph Structure**:
```
START
  ↓
preprocess_note()    - Validate input
  ↓
process_note()       - LLM classification
  ↓
store_in_database()  - Database operations
  ↓
END
```

**State Management**:
- `WorkflowState`: Extends `MessagesState`
- Tracks: `note_content`, `classification_result`, `db_result`
- Status: pending → preprocessing → processing → storing → completed

### 3. Agents

#### BaseAgent (`src/agents/base_agent.py`)

**Abstract base class** for extensible agent architecture

```python
class BaseAgent(ABC):
    - __init__(name)
    - process(input_data)  # Abstract
    - add_human_message(content)
    - add_ai_message(content)
    - get_message_history()
    - clear_history()
```

**Benefits**:
- Consistent interface across agents
- Message history tracking
- Easy to extend with new agents

#### NoteProcessorAgent (`src/agents/note_processor.py`)

**Responsibility**: LLM-based note processing

**Architecture**:
```python
__init__(model_id, quantize, device)
  ├─ Model: AutoModelForCausalLM
  ├─ Tokenizer: AutoTokenizer
  └─ Config: BitsAndBytesConfig (optional)

Methods:
  - load_model()          - Download/initialize model
  - process(note)         - Single note processing
  - process_batch(notes)  - Multiple notes
```

**Processing Flow**:
1. Load tokenizer from Hugging Face
2. Optionally apply 4-bit quantization
3. Load model to GPU/CPU
4. For each note:
   - Apply chat template
   - Generate tokens
   - Decode response
   - Parse JSON

**Key Features**:
- 4-bit quantization reduces memory 4x
- Supports both GPU and CPU
- Batch processing capability
- JSON response parsing

#### DatabaseAgent (`src/agents/database_agent.py`)

**Responsibility**: PostgreSQL database operations

**Database Schema**:
```sql
notes
├─ id (PRIMARY KEY)
├─ original_content (TEXT)
├─ created_at (TIMESTAMP)
└─ updated_at (TIMESTAMP)

classifications
├─ id (PRIMARY KEY)
├─ note_id (FOREIGN KEY)
├─ category (VARCHAR)
├─ summary (TEXT)
├─ tags (JSON)
└─ created_at (TIMESTAMP)
```

**Methods**:
```python
connect()                    - Establish DB connection
disconnect()                 - Close connection
initialize_tables()          - Create schema
process(input_data)          - Store classification
get_note(note_id)           - Retrieve single note
get_all_notes(limit)        - List recent notes
search_by_category(cat)     - Query by category
search_by_tag(tag)          - Query by tag
```

## Data Flow

### Processing a Note

```
User Input
    ↓
[ChatInterface]
    ↓
Note Content
    ↓
[WorkflowState] (START)
    ↓
[preprocess_note()] - Validate content
    ↓
[WorkflowState] (preprocessing)
    ↓
[process_note()] - Call NoteProcessorAgent
    ↓
[NoteProcessorAgent.process()]
    ├─ Apply system prompt
    ├─ Tokenize input
    ├─ Generate with LLM
    └─ Parse JSON response
    ↓
Classifications: {
    "Computer Science": {...},
    "Daily Journal": {...},
    ...
}
    ↓
[WorkflowState] (processed)
    ↓
[store_in_database()]
    ↓
[DatabaseAgent.process()]
    ├─ Insert note
    ├─ Insert classifications
    └─ Commit to DB
    ↓
[Result] {
    status: "completed",
    note_id: 123,
    categories_stored: 3
}
    ↓
[ChatInterface] - Display result
    ↓
User sees summary
```

## Classification Model

### System Prompt

The LLM receives:
```
System Prompt:
  "You are a helpful assistant..."
  "Categories: Computer Science..."
  "Output: JSON format"

User Input:
  "Today I learned about..."
```

### JSON Output Format

```json
{
  "Computer Science": {
    "Summary": "...",
    "Tags": ["tag1", "tag2"]
  },
  "Daily Journal": {
    "Summary": "...",
    "Tags": ["tag1", "tag2"]
  }
}
```

### Categories

1. **Computer Science**
   - AI, ML, Data Science
   - Bioinformatics
   - Software engineering

2. **Investments**
   - Stock market
   - Personal finance
   - Investment strategies

3. **Daily Journal**
   - Personal reflections
   - Relationships
   - Hobbies & experiences

4. **Health and Fitness**
   - Exercise routines
   - Dietary habits
   - Wellness practices

## Extensibility

### Adding a New Agent

```python
from agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)
        # Your initialization
    
    def process(self, input_data) -> Dict[str, Any]:
        # Your implementation
        self.add_ai_message("Processing...")
        result = # ... compute result
        self.add_ai_message("Done!")
        return result
```

### Adding to Workflow

```python
def custom_node(state: WorkflowState) -> WorkflowState:
    agent = CustomAgent("name")
    result = agent.process(state["data"])
    state["custom_result"] = result
    return state

workflow.add_node("custom", custom_node)
workflow.add_edge("previous", "custom")
workflow.add_edge("custom", "next")
```

### Adding a New Category

Edit `NoteProcessorAgent.system_prompt`:
```python
- New Category; description
```

### Changing LLM Model

Edit `NoteProcessorAgent.__init__()`:
```python
model_id="your-new-model-id"
```

## Performance Characteristics

### Memory Usage

| Component | Memory |
|-----------|--------|
| Base Python | ~100 MB |
| LangChain + Deps | ~200 MB |
| Model (quantized) | ~3.5 GB |
| Model (full) | ~14 GB |
| LLM Generation Buffer | ~2 GB |
| **Total (quantized)** | **~5.8 GB** |

### Speed

| Operation | Time |
|-----------|------|
| Model Download | 5-10 min |
| Model Load | 30-60 sec |
| Note Processing | 10-30 sec |
| Database Store | <1 sec |
| DB Search | <1 sec |

### Database

| Operation | Query Time |
|-----------|------------|
| Insert note | <10ms |
| Get note | <5ms |
| Search category | <50ms |
| Search tag | <100ms |

## Configuration

All settings in `src/config.py`:

```python
LLM_CONFIG = {
    "model_id": "...",
    "quantize": True,
    "device": "auto",
    "max_tokens": 1024,
}

DATABASE_CONFIG = {
    "host": "localhost",
    "database": "postgres",
    ...
}

CHAT_CONFIG = {
    "use_database": True,
    ...
}
```

## Error Handling

### Graceful Degradation

1. **Model Load Fails**: Show warning, can still use CLI
2. **DB Connection Fails**: Use `--no-db` mode
3. **LLM Parse Error**: Return raw response, log error
4. **DB Error**: Continue processing, log error

### Logging

All components log to console + optional file:
```
[timestamp] - [component] - [level] - [message]
```

## Security Considerations

1. **Database Credentials**: Use environment variables in production
2. **Model Files**: Downloaded from Hugging Face
3. **Input Validation**: Notes checked for basic validity
4. **SQL Injection**: Using parameterized queries (psycopg2)

## Testing Strategy

**Unit Tests**:
- Test each agent independently
- Mock LLM responses
- Mock database calls

**Integration Tests**:
- Full workflow execution
- With real model + DB

**Load Tests**:
- Batch processing
- Concurrent requests
