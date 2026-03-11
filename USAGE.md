# Personal Assistance System - Usage Guide

A LangChain-based note processing and classification system with a command-line chat interface and PostgreSQL database backend.

## Overview

The system processes personal notes through a multi-stage workflow:

1. **Note Input**: Users submit notes via the CLI interface
2. **Classification**: The local LLM (Phi-3.5-mini) classifies notes into categories:
   - Computer Science (AI, ML, Data Science, Biotech)
   - Investments (Stock market, finance, strategies)
   - Daily Journal (Personal reflections, experiences)
   - Health and Fitness (Exercise, diet, wellness)
3. **Summarization**: Each category receives a 2-3 sentence summary
4. **Tagging**: 3-5 relevant tags are generated for each category
5. **Storage**: Results are stored in PostgreSQL for later retrieval

## Architecture

### Class-Based Modular Components

- **BaseAgent** (`agents/base_agent.py`): Abstract base class for all agents
  - Manages message history
  - Provides common agent interface
  - Extensible for new agent types

- **NoteProcessorAgent** (`agents/note_processor.py`): LLM-based note processing
  - Loads and manages the transformer model with quantization
  - Handles note classification and summarization
  - Processes individual or batch notes

- **DatabaseAgent** (`agents/database_agent.py`): Database operations
  - Manages PostgreSQL connections
  - Stores classified notes and metadata
  - Supports searching by category or tag

- **NoteProcessingWorkflow** (`workflow.py`): LangGraph orchestration
  - Combines agents into a directed workflow
  - Manages state transitions
  - Handles preprocessing, processing, and storage

- **ChatInterface** (`chat_interface.py`): Interactive CLI
  - Command-based menu system
  - Rich terminal output formatting
  - Session management

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL:
```bash
# Create a PostgreSQL database (default: postgres)
# Update connection parameters if needed
```

3. Initialize database tables (automatic on first use):
```bash
python src/main.py
```

## Usage

### Starting the System

```bash
# Basic usage (with database)
python src/main.py

# Without database storage
python src/main.py --no-db

# Auto-load the language model on startup
python src/main.py --auto-load-model
```

### Available Commands

```
/process    - Process a new note interactively
/model      - Load/manage the language model
/database   - Manage database operations (view, search)
/search     - Search stored notes by category or tag
/history    - View notes processed in this session
/help       - Show help message
/exit       - Exit the application
```

### Workflow Examples

#### Example 1: Process a Single Note

```
> /process

Enter your note (type 'END' on a new line when done):
Today I learned about transformers and attention mechanisms. 
I also went for a run and ate healthy meals.
END

[Processing...]
✓ Note successfully classified into 3 categories:
  • Computer Science: Summary about transformers...
  • Health and Fitness: Summary about exercise and diet...
✓ Stored in database (Note ID: 1)
```

#### Example 2: Search Stored Notes

```
> /database

Database Operations:
  1. View recent notes
  2. Search by category
  3. Search by tag
  4. View specific note
  5. Back to main menu

Choose an option: 2

Enter category to search: Computer Science

Found 5 note(s) in 'Computer Science':
  Note ID: 1
  Content: Today I learned about transformers and...
  
  Note ID: 3
  Content: Exploring neural networks and backpropagation...
```

## Project Structure

```
personal-assistance/
├── src/
│   ├── main.py                 # Entry point
│   ├── chat_interface.py       # CLI interface
│   ├── workflow.py             # LangGraph workflow
│   └── agents/
│       ├── __init__.py
│       ├── base_agent.py       # Abstract base class
│       ├── note_processor.py   # LLM agent
│       └── database_agent.py   # Database agent
├── notebooks/
│   ├── model.ipynb            # Original model demonstration
│   └── operations.ipynb        # Database operations
├── requirements.txt
└── setup.sql                  # Database schema (if needed)
```

## Configuration

### Database Connection

Default PostgreSQL settings in `DatabaseAgent`:
```python
host="localhost"
database="postgres"
user="postgres"
password="postgres"
port=5432
```

To use different credentials, modify the connection parameters in `main.py`:
```python
chat = ChatInterface(
    use_db=True,
    auto_load_model=False,
)
```

### Language Model

Default model: `microsoft/Phi-3.5-mini-instruct`

To change the model, modify `NoteProcessorAgent`:
```python
self.note_processor = NoteProcessorAgent(
    model_id="your-model-id",
    quantize=True,
    device="auto"
)
```

## Features

### Agent Extensibility

Add new agents by extending `BaseAgent`:

```python
from agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)
    
    def process(self, input_data):
        # Your implementation
        pass
```

### Workflow Customization

Extend `NoteProcessingWorkflow` to add new processing stages:

```python
def new_stage(state):
    # New processing logic
    return state

workflow.add_node("new_stage", new_stage)
workflow.add_edge("process", "new_stage")
```

## Troubleshooting

### Model Loading Issues

- Ensure CUDA is available: `torch.cuda.is_available()`
- Check disk space for model downloads (~2GB)
- Use `--auto-load-model` flag for convenience

### Database Connection Errors

- Verify PostgreSQL is running
- Check connection parameters
- Run `python -c "import psycopg2; print(psycopg2.__version__)"`

### Memory Issues

- The model uses 4-bit quantization by default
- Ensure at least 8GB GPU VRAM available
- CPU fallback available (slower)

## Advanced Usage

### Batch Processing

```python
from agents.note_processor import NoteProcessorAgent

processor = NoteProcessorAgent()
processor.load_model()

notes = ["Note 1", "Note 2", "Note 3"]
result = processor.process_batch(notes)
```

### Direct API Usage

```python
from workflow import NoteProcessingWorkflow

workflow = NoteProcessingWorkflow(use_db=True)
workflow.load_model()

result = workflow.process_note("Your note here...")
```

## Performance Considerations

- **First run**: Model download (~2GB) + table creation
- **Model loading**: ~30-60 seconds depending on hardware
- **Processing time**: ~10-30 seconds per note on GPU
- **Quantization**: Reduces memory usage by ~4x with minimal accuracy loss

## Dependencies

Key packages:
- `langchain-core`: LLM framework
- `langgraph`: Workflow orchestration
- `transformers`: Hugging Face models
- `torch`: Deep learning framework
- `psycopg2`: PostgreSQL driver
- `rich`: Terminal formatting

See `requirements.txt` for complete list.
