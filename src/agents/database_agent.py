"""Database agent for storing and retrieving processed notes."""

import json
import re
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from .base_agent import BaseAgent


class DatabaseAgent(BaseAgent):
    """Agent for managing database operations (PostgreSQL)."""

    def __init__(
        self,
        host: str = "localhost",
        database: str = "personal_assistance",
        user: str = "postgres",
        password: str = "postgres",
        port: int = 5432,
    ):
        """
        Initialize the database agent.

        Args:
            host: PostgreSQL host
            database: Database name
            user: Database user
            password: Database password
            port: Database port
        """
        super().__init__(name="DatabaseManager")
        self.connection_params = {
            "host": host,
            "database": database,
            "user": user,
            "password": password,
            "port": port,
        }
        self.connection = None
        self.is_connected = False
        self.embedding_column: Optional[str] = "embedding"
        self.embedding_dim = 3072
        self.embedding_required = False

    def connect(self) -> bool:
        """
        Establish a connection to the PostgreSQL database.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            
            # Verify connection with a test query
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            
            self.is_connected = True
            print("Database connection established successfully")
            self.add_ai_message("Connected to PostgreSQL database")
            return True
            
        except psycopg2.Error as e:
            print(f"Failed to connect to database: {e}")
            self.add_ai_message(f"Database connection failed: {str(e)}")
            return False

    def disconnect(self) -> bool:
        """
        Close the database connection.

        Returns:
            True if disconnection successful, False otherwise
        """
        try:
            if self.connection:
                self.connection.close()
                self.is_connected = False
                print("Database connection closed")
                return True
        except psycopg2.Error as e:
            print(f"Error closing connection: {e}")
        return False

    def diagnose_database(self) -> Dict[str, Any]:
        """
        Diagnose database status and data availability.

        Returns:
            Dictionary with diagnostic information
        """
        if not self.is_connected:
            return {
                "connected": False,
                "error": "Not connected to database"
            }

        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Get current database and schema
            cursor.execute("SELECT current_database(), current_schema()")
            db_info = cursor.fetchone()
            
            # Get table information
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
            
            # Get column information for notes table
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'notes' AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            # Try to count notes
            cursor.execute("SELECT COUNT(*) as count FROM notes")
            result = cursor.fetchone()
            notes_count = result["count"] if result else 0
            
            # Get sample notes if any exist
            sample_notes = []
            if notes_count > 0:
                try:
                    cursor.execute("SELECT * FROM notes LIMIT 3")
                    sample_notes = cursor.fetchall()
                except Exception as e:
                    sample_notes = [{"error": str(e)}]
            
            return {
                "connected": True,
                "current_database": db_info['current_database'],
                "current_schema": db_info['current_schema'],
                "tables": tables,
                "notes_table_columns": [
                    {
                        "name": col["column_name"],
                        "type": col["data_type"],
                        "nullable": col["is_nullable"]
                    } for col in columns
                ],
                "notes_count": notes_count,
                "sample_notes": sample_notes
            }
            
        except psycopg2.Error as e:
            return {
                "connected": True,
                "error": f"Database query error: {str(e)}"
            }
        except Exception as e:
            return {
                "connected": True,
                "error": f"Unexpected error: {str(e)}"
            }
        finally:
            cursor.close()

    def initialize_tables(self) -> bool:
        """
        Verify tables exist (they should already be created via setup.sql).

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False

        try:
            cursor = self.connection.cursor()

            # Just verify the notes table exists
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'notes'
                )
            """)
            notes_table_exists = cursor.fetchone()[0]
            
            if not notes_table_exists:
                # Only create if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notes (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        mood TEXT,
                        tags TEXT[],
                        topic TEXT NOT NULL,
                        embedding VECTOR(3072)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_created_at ON notes(created_at)
                """)

            # Detect embedding column metadata from the actual schema.
            self._load_embedding_metadata(cursor)

            self.connection.commit()
            print("Database tables verified successfully")
            return True

        except psycopg2.Error as e:
            print(f"Error initializing tables: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()

    def _load_embedding_metadata(self, cursor) -> None:
        """
        Load embedding column name, nullability, and vector dimension from schema.
        Supports both 'embedding' and legacy 'embeddings' column names.
        """
        cursor.execute(
            """
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'notes'
              AND column_name IN ('embedding', 'embeddings')
            ORDER BY CASE WHEN column_name = 'embedding' THEN 0 ELSE 1 END
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        if not row:
            self.embedding_column = None
            self.embedding_dim = 3072
            self.embedding_required = False
            return

        column_name, is_nullable = row
        self.embedding_column = column_name
        self.embedding_required = (is_nullable == "NO")

        cursor.execute(
            """
            SELECT format_type(a.atttypid, a.atttypmod)
            FROM pg_attribute a
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = 'public'
              AND c.relname = 'notes'
              AND a.attname = %s
              AND a.attnum > 0
              AND NOT a.attisdropped
            """,
            (self.embedding_column,)
        )
        type_row = cursor.fetchone()
        if type_row and type_row[0]:
            match = re.search(r"vector\((\d+)\)", type_row[0])
            if match:
                self.embedding_dim = int(match.group(1))

    def _build_fallback_embedding(self, text: str) -> str:
        """
        Build a deterministic lightweight embedding vector as a pgvector literal.
        This prevents NOT NULL constraint failures when no embedding model is configured.
        """
        dim = max(1, int(self.embedding_dim or 3072))
        values = [0.0] * dim

        for idx, byte_val in enumerate(text.encode("utf-8")):
            values[idx % dim] += byte_val / 255.0

        # Keep values in a compact range.
        max_val = max(values) if values else 0.0
        if max_val > 0:
            values = [v / max_val for v in values]

        return "[" + ",".join(f"{v:.6f}" for v in values) + "]"

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store processed note in the database.

        Args:
            input_data: Dictionary containing note metadata and classifications

        Returns:
            Dictionary containing the storage results
        """
        if not self.is_connected:
            return {
                "status": "error",
                "message": "Database not connected",
            }

        try:
            cursor = self.connection.cursor()

            # Extract data from input
            note_content = input_data.get("note_content", "")
            classification = input_data.get("classification", {})

            categories_to_store = classification or {"Unclassified": {"Tags": []}}
            note_date = input_data.get("note_date", "") or datetime.now().strftime("%d-%m-%Y")
            try:
                note_timestamp = datetime.strptime(note_date, "%d-%m-%Y")
            except ValueError:
                note_timestamp = datetime.now()
                note_date = note_timestamp.strftime("%d-%m-%Y")
            note_ids = []
            topics = []
            total_tags_stored = 0

            cursor.execute(
                """
                INSERT INTO raw_notes (note, created_at)
                VALUES (%s, %s)
                """,
                (note_content, note_timestamp),
            )

            # Insert one note record per category.
            for category, data in categories_to_store.items():
                title = f"{category} {note_date}"
                topic = category
                tags = data.get("Tags", [])
                total_tags_stored += len(tags)
                content = data.get("Summary", note_content)

                if self.embedding_column:
                    embedding_vector = self._build_fallback_embedding(note_content)
                    insert_sql = f"""
                        INSERT INTO notes (title, content, topic, tags, mood, {self.embedding_column})
                        VALUES (%s, %s, %s, %s, %s, %s::vector)
                        RETURNING id
                        """
                    insert_params = (title, content, topic, tags, None, embedding_vector)
                else:
                    insert_sql = """
                        INSERT INTO notes (title, content, topic, tags, mood)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                        """
                    insert_params = (title, content, topic, tags, None)

                cursor.execute(insert_sql, insert_params)
                note_ids.append(str(cursor.fetchone()[0]))
                topics.append(topic)

            self.connection.commit()
            message = f"Stored {len(note_ids)} notes in topics: {', '.join(topics)}"
            self.add_ai_message(message)

            return {
                "status": "success",
                "note_ids": note_ids,
                "topics": topics,
                "categories_stored": len(categories_to_store),
                "tags_stored": total_tags_stored,
                "raw_note_stored": True,
            }

        except psycopg2.Error as e:
            print(f"Error storing note: {e}")
            self.connection.rollback()
            return {
                "status": "error",
                "message": f"Failed to store note: {str(e)}",
            }
        finally:
            cursor.close()

    def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a note by ID.

        Args:
            note_id: The ID of the note to retrieve (UUID string)

        Returns:
            Dictionary containing the note details, or None if not found
        """
        if not self.is_connected:
            return None

        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)

            # Get note (excluding embedding vector)
            cursor.execute(
                """
                SELECT id, title, content, topic, tags, mood, created_at, updated_at 
                FROM notes 
                WHERE id::text = %s
                """,
                (note_id,)
            )
            note = cursor.fetchone()

            if not note:
                return None

            return {
                "note_id": str(note["id"]),
                "title": note["title"],
                "content": note["content"],
                "topic": note["topic"],
                "tags": note["tags"] if note["tags"] else [],
                "mood": note["mood"],
                "created_at": note["created_at"],
                "updated_at": note["updated_at"],
            }

        except psycopg2.Error as e:
            print(f"Error retrieving note: {e}")
            return None
        finally:
            cursor.close()

    def get_all_notes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve all notes with optional limit.

        Args:
            limit: Maximum number of notes to retrieve

        Returns:
            List of notes
        """
        if not self.is_connected:
            print("Database not connected. Cannot retrieve notes.")
            return []

        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT id, title, content, topic, tags, mood, created_at, updated_at 
                FROM notes 
                ORDER BY created_at DESC 
                LIMIT %s
                """,
                (limit,)
            )
            results = cursor.fetchall()
            print(f"Query returned {len(results)} rows")
            
            notes = []
            for row in results:
                note = {
                    "note_id": str(row["id"]),
                    "title": row["title"],
                    "content": row["content"],
                    "topic": row["topic"],
                    "tags": row["tags"] if row["tags"] else [],
                    "mood": row["mood"],
                    "created_at": row["created_at"],
                }
                notes.append(note)

            print(f"Retrieved {len(notes)} complete notes")
            return notes

        except psycopg2.Error as e:
            print(f"Error retrieving notes: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            cursor.close()

    def search_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Search notes by topic/category.

        Args:
            category: The category/topic to search for

        Returns:
            List of matching notes
        """
        if not self.is_connected:
            return []

        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)

            cursor.execute(
                """
                SELECT id, title, content, topic, tags, mood, created_at 
                FROM notes 
                WHERE topic ILIKE %s
                ORDER BY created_at DESC
                """,
                (f"%{category}%",),
            )

            results = cursor.fetchall()
            notes = []

            for row in results:
                note = {
                    "note_id": str(row["id"]),
                    "title": row["title"],
                    "content": row["content"],
                    "topic": row["topic"],
                    "tags": row["tags"] if row["tags"] else [],
                    "mood": row["mood"],
                    "created_at": row["created_at"],
                }
                notes.append(note)

            return notes

        except psycopg2.Error as e:
            print(f"Error searching by category: {e}")
            return []
        finally:
            cursor.close()

    def search_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Search notes by tag in the tags array.

        Args:
            tag: The tag to search for

        Returns:
            List of notes with that tag
        """
        if not self.is_connected:
            return []

        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)

            cursor.execute(
                """
                SELECT id, title, content, topic, tags, mood, created_at 
                FROM notes 
                WHERE tags @> ARRAY[%s]
                ORDER BY created_at DESC
                """,
                (tag,),
            )

            results = cursor.fetchall()
            notes = []

            for row in results:
                note = {
                    "note_id": str(row["id"]),
                    "title": row["title"],
                    "content": row["content"],
                    "topic": row["topic"],
                    "tags": row["tags"] if row["tags"] else [],
                    "mood": row["mood"],
                    "created_at": row["created_at"],
                }
                notes.append(note)

            return notes

        except psycopg2.Error as e:
            print(f"Error searching by tag: {e}")
            return []
        finally:
            cursor.close()
