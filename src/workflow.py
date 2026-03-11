"""LangGraph-based workflow for note processing."""

from typing import Any, Dict
from datetime import datetime
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from agents.note_processor import NoteProcessorAgent
from agents.database_agent import DatabaseAgent
from config import DATABASE_CONFIG


class NoteProcessingWorkflow:
    """Orchestrates the note processing workflow using LangGraph."""

    def __init__(self, use_db: bool = True):
        """
        Initialize the workflow.

        Args:
            use_db: Whether to enable database storage
        """
        self.note_processor = NoteProcessorAgent()
        self.db_agent = DatabaseAgent(**DATABASE_CONFIG) if use_db else None
        self.use_db = use_db
        self.graph = None
        self._build_graph()

    def _build_graph(self) -> None:
        """Build the LangGraph workflow graph."""
        # Define the state schema
        class WorkflowState(MessagesState):
            note_content: str = ""
            note_date: str = ""
            classification_result: Dict[str, Any] = {}
            db_result: Dict[str, Any] = {}
            workflow_status: str = "pending"

        # Define workflow nodes
        def preprocess_note(state: WorkflowState) -> WorkflowState:
            """Preprocess and validate the note."""
            note_content = state.get("note_content", "").strip()
            note_date = state.get("note_date", "").strip()

            if not note_content:
                state["workflow_status"] = "error"
                state.setdefault("messages", []).append(
                    AIMessage(content="Error: Empty note content")
                )
                return state

            if not note_date:
                note_date = datetime.now().strftime("%d-%m-%Y")
                state["note_date"] = note_date

            state["workflow_status"] = "preprocessing"
            state.setdefault("messages", []).append(
                AIMessage(
                    content=f"Preprocessing note ({len(note_content)} characters) for date {note_date}..."
                )
            )
            return state

        def process_note(state: WorkflowState) -> WorkflowState:
            """Process the note using the NoteProcessorAgent."""
            if state["workflow_status"] == "error":
                return state

            state["workflow_status"] = "processing"
            state.setdefault("messages", []).append(
                AIMessage(content="Classifying and summarizing note...")
            )

            try:
                result = self.note_processor.process(state["note_content"])
                print(f"Classification result: {result}")
                state["classification_result"] = result
                state["workflow_status"] = "processed"

                if result["status"] == "success":
                    categories = list(result["classification"].keys())
                    state.setdefault("messages", []).append(
                        AIMessage(
                            content=f"Successfully classified note into categories: {', '.join(categories)}"
                        )
                    )
                else:
                    state.setdefault("messages", []).append(
                        AIMessage(content=f"Error processing note: {result.get('message', 'Unknown error')}")
                    )
                    state["workflow_status"] = "error"

            except Exception as e:
                state.setdefault("messages", []).append(
                    AIMessage(content=f"Exception during processing: {str(e)}")
                )
                state["workflow_status"] = "error"

            return state

        def store_in_database(state: WorkflowState) -> WorkflowState:
            """Store the processed result in the database."""
            if not self.use_db or state["workflow_status"] == "error":
                state["workflow_status"] = "completed"
                return state

            state["workflow_status"] = "storing"
            state.setdefault("messages", []).append(AIMessage(content="Storing result in database..."))

            try:
                if not self.db_agent.is_connected:
                    self.db_agent.connect()
                    self.db_agent.initialize_tables()

                db_input = {
                    **state["classification_result"],
                    "note_date": state.get("note_date", ""),
                }
                result = self.db_agent.process(db_input)
                state["db_result"] = result
                state["workflow_status"] = "completed"

                if result["status"] == "success":
                    state.setdefault("messages", []).append(
                        AIMessage(
                            content=f"Successfully stored {len(result.get('note_ids', []))} notes for {result['categories_stored']} categories"
                        )
                    )
                else:
                    state.setdefault("messages", []).append(
                        AIMessage(content=f"Error storing in database: {result.get('message', 'Unknown error')}")
                    )
                    state["workflow_status"] = "error"

            except Exception as e:
                state.setdefault("messages", []).append(
                    AIMessage(content=f"Exception during storage: {str(e)}")
                )
                state["workflow_status"] = "error"

            return state

        # Build the graph
        workflow = StateGraph(WorkflowState)
        workflow.add_node("preprocess", preprocess_note)
        workflow.add_node("process", process_note)
        workflow.add_node("store", store_in_database)

        workflow.add_edge(START, "preprocess")
        workflow.add_edge("preprocess", "process")
        workflow.add_edge("process", "store")
        workflow.add_edge("store", END)

        self.graph = workflow.compile()

    def process_note(self, note_content: str, note_date: str = "") -> Dict[str, Any]:
        """
        Process a note through the entire workflow.

        Args:
            note_content: The content of the note to process
            note_date: Date associated with the note in DD-MM-YYYY format

        Returns:
            Dictionary containing the final workflow result
        """
        initial_state = {
            "messages": [HumanMessage(content=note_content)],
            "note_content": note_content,
            "note_date": note_date,
            "classification_result": {},
            "db_result": {},
            "workflow_status": "pending",
        }

        final_state = self.graph.invoke(initial_state)

        return {
            "status": final_state["workflow_status"],
            "classifications": final_state.get("classification_result", {}),
            "database_result": final_state.get("db_result", {}),
            "messages": final_state.get("messages", []),
        }

    def load_model(self) -> None:
        """Load the language model."""
        self.note_processor.load_model()

    def disconnect(self) -> None:
        """Clean up resources."""
        if self.db_agent and self.db_agent.is_connected:
            self.db_agent.disconnect()
