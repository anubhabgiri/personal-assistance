"""Command-line interface for the personal assistance system."""

import json
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from workflow import NoteProcessingWorkflow
from agents.database_agent import DatabaseAgent


class ChatInterface:
    """Interactive command-line chat interface for the system."""

    def __init__(self, use_db: bool = True, auto_load_model: bool = False):
        """
        Initialize the chat interface.

        Args:
            use_db: Whether to enable database storage
            auto_load_model: Whether to automatically load the model on startup
        """
        self.console = Console()
        self.workflow = NoteProcessingWorkflow(use_db=use_db)
        self.db_agent = self.workflow.db_agent
        self.model_loaded = False
        self.session_notes = []

        if auto_load_model:
            self.load_model()

    def print_welcome(self) -> None:
        """Print the welcome message."""
        welcome_text = """
+----------------------------------------------------------------+
|          Personal Assistance Note Processing System            |
|                    Powered by LangChain & LLM                  |
+----------------------------------------------------------------+

Available Commands:
  /process    - Process a new note
  /model      - Load/manage the language model
  /database   - Manage database operations
  /search     - Search stored notes
  /history    - View session history
  /help       - Show this help message
  /exit       - Exit the application
"""
        self.console.print(welcome_text, style="cyan bold")

    def load_model(self) -> None:
        """Load the language model."""
        if self.model_loaded:
            self.console.print("Model is already loaded!", style="yellow")
            return

        try:
            with self.console.status("[bold green]Loading model...", spinner="dots"):
                self.workflow.load_model()
            self.model_loaded = True
            self.console.print(
                "Model loaded successfully!",
                style="green bold",
            )
        except Exception as e:
            self.console.print(f"Error loading model: {str(e)}", style="red bold")

    def process_note_interactive(self) -> None:
        """Interactive note processing."""
        note_date = self._prompt_note_date()
        if note_date is None:
            return

        self.console.print("\n[bold blue]Enter your note (type 'END' on a new line when done):[/bold blue]")

        lines = []
        while True:
            try:
                line = self.console.input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Note entry cancelled.[/yellow]")
                return

        note_content = "\n".join(lines)

        if not note_content.strip():
            self.console.print("[yellow]Note is empty, skipping.[/yellow]")
            return

        if not self.model_loaded:
            self.console.print("[yellow]Loading model first...[/yellow]")
            self.load_model()

        if not self.model_loaded:
            self.console.print("[red]Cannot process note without model. Exiting.[/red]")
            return

        # Process the note
        with self.console.status("[bold green]Processing note...", spinner="dots"):
            result = self.workflow.process_note(note_content, note_date=note_date)

        # Display results
        self._display_process_result(result)

        # Store in session
        self.session_notes.append({
            "note": note_content,
            "note_date": note_date,
            "result": result,
        })

    def _prompt_note_date(self) -> Optional[str]:
        """Prompt for an optional note date and return it in DD-MM-YYYY format."""
        default_date = datetime.now().strftime("%d-%m-%Y")
        self.console.print(
            f"\n[bold blue]Enter note date in DD-MM-YYYY format (press Enter for {default_date}):[/bold blue]"
        )

        while True:
            try:
                raw_value = self.console.input().strip()
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Note entry cancelled.[/yellow]")
                return None

            if not raw_value:
                return default_date

            try:
                parsed_date = datetime.strptime(raw_value, "%d-%m-%Y")
                return parsed_date.strftime("%d-%m-%Y")
            except ValueError:
                self.console.print("[yellow]Invalid date. Use DD-MM-YYYY.[/yellow]")

    def _display_process_result(self, result: dict) -> None:
        """Display the processing result."""
        status = result.get("status", "unknown")
        status_style = "green" if status == "completed" else "red" if status == "error" else "yellow"

        panel = Panel(
            f"[{status_style} bold]Status: {status.upper()}[/]",
            title="Process Result",
            expand=False,
        )
        self.console.print(panel)

        # Display classifications
        classifications = result.get("classifications", {})
        if classifications.get("classification"):
            self.console.print("\n[bold cyan]Classifications:[/bold cyan]")
            classification_data = classifications["classification"]

            for category, data in classification_data.items():
                summary = data.get("Summary", "N/A")
                tags = data.get("Tags", [])

                self.console.print(f"\n  [bold yellow]{category}[/bold yellow]")
                self.console.print(f"    Summary: {summary}")
                self.console.print(f"    Tags: {', '.join(tags)}")

        # Display database result
        db_result = result.get("database_result", {})
        if db_result and db_result.get("status") == "success":
            note_ids = db_result.get("note_ids", [])
            self.console.print(
                f"\n[bold green]Stored {len(note_ids)} record(s) in database[/bold green]"
            )
            if note_ids:
                self.console.print(f"  Note IDs: {', '.join(note_ids)}")
            if "topics" in db_result:
                self.console.print(f"  Topics: {', '.join(db_result['topics'])}")
            if "tags_stored" in db_result:
                self.console.print(f"  Tags stored: {db_result['tags_stored']}")

        # Display messages
        messages = result.get("messages", [])
        if messages:
            self.console.print("\n[bold cyan]Workflow Messages:[/bold cyan]")
            for msg in messages:
                content = msg.content if hasattr(msg, "content") else str(msg)
                self.console.print(f"  * {content}")

    def database_operations(self) -> None:
        """Interactive database operations menu."""
        if not self.db_agent or not self.db_agent.is_connected:
            self.console.print("[yellow]Connecting to database...[/yellow]")
            if not self.db_agent.connect():
                self.console.print("[red]Failed to connect to database.[/red]")
                return
            if not self.db_agent.initialize_tables():
                self.console.print("[red]Failed to initialize database tables.[/red]")
                return

        while True:
            self.console.print("\n[bold blue]Database Operations:[/bold blue]")
            self.console.print("  1. View recent notes")
            self.console.print("  2. Search by category")
            self.console.print("  3. Search by tag")
            self.console.print("  4. View specific note")
            self.console.print("  5. Diagnose database")
            self.console.print("  6. Back to main menu")

            choice = self.console.input("[bold cyan]Choose an option (1-6):[/bold cyan] ").strip()

            if choice == "1":
                self._view_recent_notes()
            elif choice == "2":
                self._search_by_category()
            elif choice == "3":
                self._search_by_tag()
            elif choice == "4":
                self._view_specific_note()
            elif choice == "5":
                self._diagnose_database()
            elif choice == "6":
                break
            else:
                self.console.print("[yellow]Invalid choice. Please try again.[/yellow]")

    def _view_recent_notes(self) -> None:
        """View recent notes."""
        notes = self.db_agent.get_all_notes(limit=5)

        if not notes:
            self.console.print("[yellow]No notes found.[/yellow]")
            return

        for note in notes:
            self.console.print(f"\n[bold cyan]Note ID: {note['note_id']}[/bold cyan]")
            self.console.print(f"[bold]Title:[/bold] {note['title']}")
            self.console.print(f"[bold]Topic:[/bold] {note['topic']}")
            self.console.print(f"[bold]Created:[/bold] {note['created_at']}")
            self.console.print(f"[bold]Content:[/bold] {note['content'][:100]}...")

            if note["tags"]:
                self.console.print(f"[bold]Tags:[/bold] {', '.join(note['tags'])}")

    def _search_by_category(self) -> None:
        """Search notes by category/topic."""
        category = self.console.input("[bold cyan]Enter topic to search:[/bold cyan] ").strip()

        if not category:
            self.console.print("[yellow]Topic cannot be empty.[/yellow]")
            return

        notes = self.db_agent.search_by_category(category)

        if not notes:
            self.console.print(f"[yellow]No notes found for topic '{category}'.[/yellow]")
            return

        self.console.print(f"\n[bold cyan]Found {len(notes)} note(s) in topic '{category}':[/bold cyan]")
        for note in notes:
            self.console.print(f"\n  [bold]Title:[/bold] {note['title']}")
            self.console.print(f"  [bold]Topic:[/bold] {note['topic']}")
            self.console.print(f"  [bold]Content:[/bold] {note['content'][:100]}...")

    def _search_by_tag(self) -> None:
        """Search notes by tag."""
        tag = self.console.input("[bold cyan]Enter tag to search:[/bold cyan] ").strip()

        if not tag:
            self.console.print("[yellow]Tag cannot be empty.[/yellow]")
            return

        notes = self.db_agent.search_by_tag(tag)

        if not notes:
            self.console.print(f"[yellow]No notes found with tag '{tag}'.[/yellow]")
            return

        self.console.print(f"\n[bold cyan]Found {len(notes)} note(s) with tag '{tag}':[/bold cyan]")
        for note in notes:
            self.console.print(f"\n  [bold]Title:[/bold] {note['title']}")
            self.console.print(f"  [bold]Tags:[/bold] {', '.join(note['tags'])}")
            self.console.print(f"  [bold]Content:[/bold] {note['content'][:100]}...")

    def _view_specific_note(self) -> None:
        """View a specific note by ID."""
        try:
            note_id = self.console.input("[bold cyan]Enter note ID:[/bold cyan] ").strip()
            note = self.db_agent.get_note(note_id)

            if not note:
                self.console.print(f"[yellow]Note {note_id} not found.[/yellow]")
                return

            self.console.print(f"\n[bold cyan]Note {note_id}[/bold cyan]")
            self.console.print(f"[bold]Title:[/bold] {note['title']}")
            self.console.print(f"[bold]Topic:[/bold] {note['topic']}")
            self.console.print(f"[bold]Created:[/bold] {note['created_at']}")
            self.console.print(f"[bold]Updated:[/bold] {note['updated_at']}")

            if note["mood"]:
                self.console.print(f"[bold]Mood:[/bold] {note['mood']}")

            if note["tags"]:
                self.console.print(f"[bold]Tags:[/bold] {', '.join(note['tags'])}")

            self.console.print(f"\n[bold]Content:[/bold]\n{note['content']}")

        except Exception as e:
            self.console.print(f"[red]Error: {str(e)}[/red]")

    def _diagnose_database(self) -> None:
        """Diagnose database status and data availability."""
        self.console.print("\n[bold blue]Diagnosing database...[/bold blue]")

        diagnosis = self.db_agent.diagnose_database()

        if not diagnosis.get("connected"):
            self.console.print(f"[red]Database not connected: {diagnosis.get('error')}[/red]")
            return

        if "error" in diagnosis:
            self.console.print(f"[red]Diagnostic error: {diagnosis['error']}[/red]")
            return

        self.console.print("\n[bold cyan]Database Connection Info:[/bold cyan]")
        self.console.print(f"  Database: {diagnosis.get('current_database', 'Unknown')}")
        self.console.print(f"  Schema: {diagnosis.get('current_schema', 'Unknown')}")

        self.console.print("\n[bold cyan]Tables in schema:[/bold cyan]")
        for table in diagnosis.get("tables", []):
            self.console.print(f"  * {table}")

        self.console.print("\n[bold cyan]Notes table columns:[/bold cyan]")
        for col in diagnosis.get("notes_table_columns", []):
            nullable = "nullable" if col["nullable"] == "YES" else "NOT NULL"
            self.console.print(f"  * {col['name']}: {col['type']} ({nullable})")

        self.console.print(f"\n[bold cyan]Total notes in database: {diagnosis['notes_count']}[/bold cyan]")

        if diagnosis["sample_notes"] and (
            not isinstance(diagnosis["sample_notes"][0], dict)
            or "error" not in diagnosis["sample_notes"][0]
        ):
            self.console.print("\n[bold cyan]Sample notes found:[/bold cyan]")
            for note in diagnosis["sample_notes"][:3]:
                if isinstance(note, dict) and "error" not in note:
                    self.console.print(f"\n  Note ID: {note.get('id', 'N/A')}")
                    # Try to display whatever columns are available
                    for key, value in note.items():
                        if key != "id":
                            self.console.print(f"    {key}: {str(value)[:100]}")
        else:
            self.console.print("\n[yellow]No notes found in the database.[/yellow]")

    def view_session_history(self) -> None:
        """View notes processed in this session."""
        if not self.session_notes:
            self.console.print("[yellow]No notes processed in this session.[/yellow]")
            return

        self.console.print(f"\n[bold cyan]Session History ({len(self.session_notes)} notes):[/bold cyan]")

        for i, session_note in enumerate(self.session_notes, 1):
            self.console.print(f"\n[bold yellow]Note {i}:[/bold yellow]")
            self.console.print(f"Content: {session_note['note'][:100]}...")

            result = session_note["result"]
            classifications = result.get("classifications", {}).get("classification", {})
            if classifications:
                self.console.print(f"Categories: {', '.join(classifications.keys())}")

    def run(self) -> None:
        """Run the main chat loop."""
        self.print_welcome()

        while True:
            try:
                command = self.console.input(
                    "\n[bold cyan]Enter command (type /help for options):[/bold cyan] "
                ).strip()

                if not command:
                    continue

                if command == "/help":
                    self.print_welcome()
                elif command == "/process":
                    self.process_note_interactive()
                elif command == "/model":
                    self.load_model()
                elif command == "/database":
                    self.database_operations()
                elif command == "/history":
                    self.view_session_history()
                elif command == "/search":
                    self.database_operations()
                elif command == "/exit" or command == "/quit":
                    self.console.print("[yellow]Goodbye![/yellow]")
                    self.workflow.disconnect()
                    break
                else:
                    self.console.print("[red]Unknown command. Type /help for available commands.[/red]")

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted. Type /exit to quit.[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")
