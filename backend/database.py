"""
SQLite database layer for LLM Council.
Replaces JSON file storage with proper database.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from schemas import CouncilMetrics


class Database:
    """SQLite database for conversations and metrics"""
    
    def __init__(self, db_path: str = "data/council.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        with self.get_connection() as conn:
            # Conversations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT,
                    stage1 TEXT,
                    stage2 TEXT,
                    stage3 TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)
            
            # Query metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_hash TEXT NOT NULL,
                    conversation_id TEXT,
                    total_cost_usd REAL,
                    total_time_ms INTEGER,
                    models_queried INTEGER,
                    models_succeeded INTEGER,
                    agreement_score REAL,
                    confidence_mean REAL,
                    confidence_std REAL,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_id ON messages(conversation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_query_hash ON query_metrics(query_hash)")
    
    # Conversation methods
    def create_conversation(self, conv_id: Optional[str] = None) -> str:
        conv_id = conv_id or str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO conversations (id, created_at, updated_at)
                VALUES (?, ?, ?)
            """, (conv_id, now, now))
        
        return conv_id
    
    def get_conversation(self, conv_id: str) -> Optional[dict]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conv_id,)
            ).fetchone()
            
            if not row:
                return None
            
            messages = conn.execute("""
                SELECT * FROM messages WHERE conversation_id = ?
                ORDER BY created_at ASC
            """, (conv_id,)).fetchall()
            
            return {
                "id": row["id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "messages": [self._row_to_message(m) for m in messages]
            }
    
    def list_conversations(self, limit: int = 50) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM conversations
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def delete_conversation(self, conv_id: str):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
            conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    
    # Message methods
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: Optional[str] = None,
        stage1: Optional[list] = None,
        stage2: Optional[list] = None,
        stage3: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> int:
        now = datetime.utcnow().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO messages 
                (conversation_id, role, content, stage1, stage2, stage3, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conversation_id,
                role,
                content,
                json.dumps(stage1) if stage1 else None,
                json.dumps(stage2) if stage2 else None,
                stage3,
                json.dumps(metadata) if metadata else None,
                now
            ))
            
            # Update conversation timestamp
            conn.execute("""
                UPDATE conversations SET updated_at = ? WHERE id = ?
            """, (now, conversation_id))
            
            return cursor.lastrowid
    
    def _row_to_message(self, row) -> dict:
        return {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "stage1": json.loads(row["stage1"]) if row["stage1"] else None,
            "stage2": json.loads(row["stage2"]) if row["stage2"] else None,
            "stage3": row["stage3"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
            "created_at": row["created_at"]
        }
    
    # Metrics methods
    def record_metrics(self, metrics: CouncilMetrics, conversation_id: Optional[str] = None):
        now = datetime.utcnow().isoformat()
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO query_metrics
                (query_hash, conversation_id, total_cost_usd, total_time_ms,
                 models_queried, models_succeeded, agreement_score,
                 confidence_mean, confidence_std, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.query_hash,
                conversation_id,
                metrics.total_cost_usd,
                metrics.total_time_ms,
                metrics.models_queried,
                metrics.models_succeeded,
                metrics.agreement_score,
                metrics.confidence_mean,
                metrics.confidence_std,
                now
            ))
    
    def get_aggregate_metrics(self) -> dict:
        with self.get_connection() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total_queries,
                    SUM(total_cost_usd) as total_cost,
                    AVG(total_time_ms) as avg_time_ms,
                    AVG(agreement_score) as avg_agreement,
                    AVG(confidence_mean) as avg_confidence
                FROM query_metrics
            """).fetchone()
            
            return dict(row) if row else {}


# Global instance
_db: Optional[Database] = None


def get_database() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db
