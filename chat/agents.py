"""Agent adapters for the chat tool.

To plug in a new agent: subclass `Agent`, implement `send()`, and add it to `AGENTS`.
An agent can reply with `options`; the chat shows them as a selectable menu and
sends the chosen option back to the agent as the next message.
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Make the project's `src/` importable (its modules use top-level imports like `from agents ...`).
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@dataclass
class Reply:
    text: str
    options: list = field(default_factory=list)


class Agent:
    """Minimal interface every chat agent implements."""

    name = "agent"
    description = ""

    def connect(self) -> None:
        """Called once when the user selects this agent (load models, open connections...)."""

    def send(self, message: str) -> Reply:
        raise NotImplementedError

    def disconnect(self) -> None:
        """Called when switching away or exiting."""


class EchoAgent(Agent):
    """A dependency-free agent for trying out the chat tool."""

    name = "echo"
    description = "Echoes your messages back (no setup needed)"

    def send(self, message: str) -> Reply:
        if message.endswith("?"):
            return Reply(f"You asked: {message!r}. Pick an answer:", ["Yes", "No", "Maybe"])
        return Reply(f"Echo: {message}")


class NotesAgent(Agent):
    """Classifies & summarises a note using the project's LangGraph workflow."""

    name = "notes"
    description = "Classify, summarise and store a note (LLM + Postgres)"

    def __init__(self):
        self.workflow = None

    def connect(self) -> None:
        from workflow import NoteProcessingWorkflow

        self.workflow = NoteProcessingWorkflow(use_db=True)
        if self.workflow.db_agent and not self.workflow.db_agent.connect():
            print("Continuing without database storage.")
            self.workflow.db_agent = None
            self.workflow.use_db = False
        print("Loading language model, this can take a while...")
        self.workflow.load_model()

    def send(self, message: str) -> Reply:
        result = self.workflow.process_note(message, datetime.now().strftime("%d-%m-%Y"))
        lines = [f"Status: {result['status']}"]
        for category, info in (result.get("classifications") or {}).items():
            if isinstance(info, dict):
                lines.append(f"\n[{category}]\n  {info.get('Summary', '')}")
                lines.append(f"  Tags: {', '.join(info.get('Tags', []))}")
        for msg in result.get("messages", [])[1:]:  # skip echo of the human note
            lines.append(f"- {getattr(msg, 'content', msg)}")
        return Reply("\n".join(lines))

    def disconnect(self) -> None:
        if self.workflow:
            self.workflow.disconnect()


class SearchAgent(Agent):
    """Searches stored notes via the project's DatabaseAgent."""

    name = "search"
    description = "Search stored notes by tag or category (Postgres)"
    MODES = ["By tag", "By category", "Cancel"]

    def __init__(self):
        self.db = None
        self.pending_query = None

    def connect(self) -> None:
        from agents.database_agent import DatabaseAgent
        from config import DATABASE_CONFIG

        self.db = DatabaseAgent(**DATABASE_CONFIG)
        if not self.db.connect():
            raise RuntimeError("Could not connect to the database")

    def send(self, message: str) -> Reply:
        # Second step: the user picked how to search.
        if self.pending_query is not None and message in self.MODES:
            query, self.pending_query = self.pending_query, None
            if message == "Cancel":
                return Reply("Search cancelled.")
            search = self.db.search_by_tag if message == "By tag" else self.db.search_by_category
            return Reply(self._format(search(query)))

        if message.lower() in ("recent", "latest"):
            return Reply(self._format(self.db.get_all_notes(limit=10)))

        # First step: ask how to interpret the query.
        self.pending_query = message
        return Reply(f"How should I search for {message!r}?", self.MODES)

    @staticmethod
    def _format(notes: list) -> str:
        if not notes:
            return "No notes found."
        out = [f"Found {len(notes)} note(s):"]
        for n in notes:
            tags = ", ".join(n.get("tags") or [])
            out.append(f"\n• {n.get('title') or n.get('topic')}  ({n.get('created_at')})")
            out.append(f"  {n.get('content', '')}")
            if tags:
                out.append(f"  Tags: {tags}")
        return "\n".join(out)

    def disconnect(self) -> None:
        if self.db and self.db.is_connected:
            self.db.disconnect()


# Registry of available agents: add your own here.
AGENTS = [NotesAgent, SearchAgent, EchoAgent]

