import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from roblox_panel.models import MetricSnapshot


DEFAULT_DB_PATH = Path.home() / ".roblox_panel" / "panel.db"


class Storage:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS universes (
                    universe_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    root_place_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metric_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    universe_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    player_count INTEGER NOT NULL,
                    server_count INTEGER NOT NULL,
                    avg_fps REAL NOT NULL,
                    avg_ping REAL NOT NULL
                )
            """)

    def set_api_key(self, api_key: str):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES ('open_cloud_api_key', ?)",
                (api_key,)
            )

    def get_api_key(self) -> Optional[str]:
        cur = self.get_connection().cursor()
        cur.execute("SELECT value FROM config WHERE key = 'open_cloud_api_key'")
        row = cur.fetchone()
        return row["value"] if row else None

    def save_universe(self, universe_id: int, name: str, root_place_id: int):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO universes (universe_id, name, root_place_id) VALUES (?, ?, ?)",
                (universe_id, name, root_place_id)
            )

    def list_universes(self) -> List[Tuple[int, str, int]]:
        cur = self.get_connection().cursor()
        cur.execute("SELECT universe_id, name, root_place_id FROM universes ORDER BY universe_id DESC")
        return [(r["universe_id"], r["name"], r["root_place_id"]) for r in cur.fetchall()]

    def record_snapshot(self, snapshot: MetricSnapshot):
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO metric_history (universe_id, timestamp, player_count, server_count, avg_fps, avg_ping)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.universe_id,
                    snapshot.timestamp.isoformat(),
                    snapshot.player_count,
                    snapshot.server_count,
                    snapshot.avg_fps,
                    snapshot.avg_ping,
                )
            )

    def get_recent_metrics(self, universe_id: int, limit: int = 50) -> List[MetricSnapshot]:
        cur = self.get_connection().cursor()
        cur.execute(
            """
            SELECT timestamp, universe_id, player_count, server_count, avg_fps, avg_ping
            FROM metric_history
            WHERE universe_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (universe_id, limit)
        )
        rows = cur.fetchall()
        out = []
        for r in reversed(rows):
            out.append(MetricSnapshot(
                timestamp=datetime.fromisoformat(r["timestamp"]),
                universe_id=r["universe_id"],
                player_count=r["player_count"],
                server_count=r["server_count"],
                avg_fps=r["avg_fps"],
                avg_ping=r["avg_ping"]
            ))
        return out

    def prune_old_metrics(self, days: int = 7):
        # SQLite modifier string e.g. '-7 days'
        modifier = f"-{days} days"
        with self.get_connection() as conn:
            conn.execute(
                "DELETE FROM metric_history WHERE timestamp < datetime('now', ?)",
                (modifier,)
            )

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
