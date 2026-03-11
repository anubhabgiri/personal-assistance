"""Configuration for the Personal Assistance System.

This file contains all configurable parameters for the system.
Modify as needed for your setup.
"""

# Language Model Configuration
LLM_CONFIG = {
    "model_id": "microsoft/Phi-3.5-mini-instruct",
    "quantize": True,  # Use 4-bit quantization to reduce memory
    "device": "auto",  # "cuda", "cpu", or "auto"
    "max_tokens": 1024,  # Maximum tokens to generate
}

# Database Configuration
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "personal_assistance",
    "user": "postgres",
    "password": "postgres",
}

# Chat Interface Configuration
CHAT_CONFIG = {
    "use_database": True,  # Enable database storage
    "auto_load_model": False,  # Load model on startup
    "rich_console": True,  # Use rich formatting for output
}

# System Prompt for Note Classification
SYSTEM_PROMPT = """
You are a helpful assistant that classifies notes into categories and summarizes them.

Categories:
1. Computer Science: AI, ML, Data Science, software engineering
2. Investments: Stock market, finance, investment strategies
3. Daily Journal: Personal reflections, thoughts, experiences
4. Health and Fitness: Exercise, diet, wellness practices

For each applicable category:
- Provide a 2-3 sentence summary
- Generate 3-5 relevant tags

Return ONLY valid JSON with categories as keys.
"""

# Logging Configuration
LOG_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "system.log",
}

# Session Configuration
SESSION_CONFIG = {
    "max_history": 100,  # Maximum messages to keep in history
    "save_on_exit": True,  # Save session to file on exit
    "session_file": "session_history.json",
}


def get_llm_config():
    """Get language model configuration."""
    return LLM_CONFIG


def get_database_config():
    """Get database configuration."""
    return DATABASE_CONFIG


def get_chat_config():
    """Get chat interface configuration."""
    return CHAT_CONFIG


def get_system_prompt():
    """Get the system prompt for note classification."""
    return SYSTEM_PROMPT


if __name__ == "__main__":
    # Print current configuration
    import json

    print("=== Current Configuration ===\n")
    print("LLM Configuration:")
    print(json.dumps(LLM_CONFIG, indent=2))
    print("\nDatabase Configuration:")
    print(json.dumps(DATABASE_CONFIG, indent=2))
    print("\nChat Configuration:")
    print(json.dumps(CHAT_CONFIG, indent=2))
