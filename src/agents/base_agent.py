"""Base agent class for extensible agent architecture."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class BaseAgent(ABC):
    """Abstract base class for all agents in the system."""

    def __init__(self, name: str):
        """
        Initialize the base agent.

        Args:
            name: The name of the agent
        """
        self.name = name
        self.message_history: List[BaseMessage] = []

    @abstractmethod
    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Process input data and return output.

        Args:
            input_data: The input data to process

        Returns:
            Dictionary containing the processing results
        """
        pass

    def add_human_message(self, content: str) -> None:
        """
        Add a human message to the conversation history.

        Args:
            content: The message content
        """
        self.message_history.append(HumanMessage(content=content))

    def add_ai_message(self, content: str) -> None:
        """
        Add an AI message to the conversation history.

        Args:
            content: The message content
        """
        self.message_history.append(AIMessage(content=content))

    def get_message_history(self) -> List[BaseMessage]:
        """
        Get the message history.

        Returns:
            List of messages
        """
        return self.message_history

    def clear_history(self) -> None:
        """Clear the message history."""
        self.message_history = []

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
