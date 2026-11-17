"""Persistência do estado do aluno em SQLite (stdlib, sem ORM)."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import UTC, datetime


class LearnerStore:
    def __init__(self, path: str = ":memory:"):
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS learners ("
            "id TEXT PRIMARY KEY, state TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        self._conn.commit()

    def create(self, state: dict) -> str:
        learner_id = uuid.uuid4().hex[:12]
        self.save(learner_id, state)
        return learner_id

    def load(self, learner_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT state FROM learners WHERE id = ?", (learner_id,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, learner_id: str, state: dict) -> None:
        now = datetime.now(UTC).isoformat()
        with self._lock:
            self._conn.execute(
                "INSERT INTO learners (id, state, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET state = excluded.state, updated_at = excluded.updated_at",
                (learner_id, json.dumps(state, ensure_ascii=False), now),
            )
            self._conn.commit()
