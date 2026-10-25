"""SQLite persistence layer. All queries are parameterised."""
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age_group TEXT NOT NULL DEFAULT 'mid',
    suit_color TEXT NOT NULL DEFAULT 'white',
    visor_color TEXT NOT NULL DEFAULT 'gold',
    xp INTEGER NOT NULL DEFAULT 0,
    skill REAL NOT NULL DEFAULT 0.5,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_played TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS settings (
    profile_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (profile_id, key),
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS mission_progress (
    profile_id INTEGER NOT NULL,
    mission_id TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    best_stars INTEGER NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (profile_id, mission_id),
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS achievements (
    profile_id INTEGER NOT NULL,
    achievement_id TEXT NOT NULL,
    earned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (profile_id, achievement_id),
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    mission_id TEXT NOT NULL,
    mistakes INTEGER NOT NULL,
    hints INTEGER NOT NULL,
    seconds REAL NOT NULL,
    tier TEXT NOT NULL,
    skill_after REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);
"""

AGE_GROUPS = ("young", "mid", "teen")


class Database:
    def __init__(self, path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._memory_conn = (sqlite3.connect(":memory:", check_same_thread=False)
                             if self.path == ":memory:" else None)
        self.init_schema()

    def _connect(self):
        conn = self._memory_conn or sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _run(self, sql: str, params: tuple = (), fetch: Optional[str] = None):
        conn = self._connect()
        try:
            with conn:  # commit / rollback
                cur = conn.execute(sql, params)
                if fetch == "one":
                    row = cur.fetchone()
                    return dict(row) if row else None
                if fetch == "all":
                    return [dict(r) for r in cur.fetchall()]
                return cur.lastrowid
        finally:
            if self._memory_conn is None:
                conn.close()

    def init_schema(self):
        conn = self._connect()
        try:
            with conn:
                conn.executescript(SCHEMA)
        finally:
            if self._memory_conn is None:
                conn.close()

    # profiles
    def create_profile(self, name, age_group="mid", suit_color="white", visor_color="gold") -> int:
        name = (name or "").strip()[:20]
        if not name:
            raise ValueError("Profile name cannot be empty")
        if age_group not in AGE_GROUPS:
            raise ValueError(f"age_group must be one of {AGE_GROUPS}")
        return self._run(
            "INSERT INTO profiles (name, age_group, suit_color, visor_color) VALUES (?,?,?,?)",
            (name, age_group, suit_color, visor_color))

    def get_profile(self, profile_id: int) -> Optional[Dict[str, Any]]:
        return self._run("SELECT * FROM profiles WHERE id=?", (profile_id,), "one")

    def list_profiles(self) -> List[Dict[str, Any]]:
        return self._run("SELECT * FROM profiles ORDER BY last_played DESC, id DESC", (), "all")

    def touch_profile(self, profile_id: int):
        self._run("UPDATE profiles SET last_played=CURRENT_TIMESTAMP WHERE id=?", (profile_id,))

    def delete_profile(self, profile_id: int):
        self._run("DELETE FROM profiles WHERE id=?", (profile_id,))

    def add_xp(self, profile_id: int, amount: int) -> int:
        self._run("UPDATE profiles SET xp = MAX(0, xp + ?) WHERE id=?", (int(amount), profile_id))
        return self.get_profile(profile_id)["xp"]

    def set_skill(self, profile_id: int, skill: float):
        self._run("UPDATE profiles SET skill=? WHERE id=?", (max(0.0, min(1.0, skill)), profile_id))

    # settings
    def set_setting(self, profile_id: int, key: str, value):
        self._run("INSERT INTO settings (profile_id,key,value) VALUES (?,?,?) "
                  "ON CONFLICT(profile_id,key) DO UPDATE SET value=excluded.value",
                  (profile_id, key, str(value)))

    def get_setting(self, profile_id: int, key: str, default=None):
        row = self._run("SELECT value FROM settings WHERE profile_id=? AND key=?",
                        (profile_id, key), "one")
        return row["value"] if row else default

    # mission progress
    def get_progress(self, profile_id: int) -> Dict[str, Dict[str, Any]]:
        rows = self._run("SELECT * FROM mission_progress WHERE profile_id=?", (profile_id,), "all")
        return {r["mission_id"]: r for r in rows}

    def completed_missions(self, profile_id: int) -> set:
        return {m for m, r in self.get_progress(profile_id).items() if r["completed"]}

    def record_attempt(self, profile_id: int, mission_id: str):
        self._run("INSERT INTO mission_progress (profile_id,mission_id,attempts) VALUES (?,?,1) "
                  "ON CONFLICT(profile_id,mission_id) DO UPDATE SET attempts=attempts+1",
                  (profile_id, mission_id))

    def record_completion(self, profile_id: int, mission_id: str, stars: int):
        self._run("INSERT INTO mission_progress (profile_id,mission_id,completed,best_stars) "
                  "VALUES (?,?,1,?) ON CONFLICT(profile_id,mission_id) DO UPDATE SET "
                  "completed=1, best_stars=MAX(best_stars, excluded.best_stars)",
                  (profile_id, mission_id, stars))

    # achievements
    def grant_achievement(self, profile_id: int, achievement_id: str) -> bool:
        """True only if newly granted."""
        if achievement_id in self.list_achievements(profile_id):
            return False
        self._run("INSERT OR IGNORE INTO achievements (profile_id,achievement_id) VALUES (?,?)",
                  (profile_id, achievement_id))
        return True

    def list_achievements(self, profile_id: int) -> List[str]:
        rows = self._run("SELECT achievement_id FROM achievements WHERE profile_id=?",
                         (profile_id,), "all")
        return [r["achievement_id"] for r in rows]

    # learning performance
    def record_performance(self, profile_id, mission_id, mistakes, hints, seconds, tier, skill_after):
        self._run("INSERT INTO performance (profile_id,mission_id,mistakes,hints,seconds,tier,skill_after) "
                  "VALUES (?,?,?,?,?,?,?)",
                  (profile_id, mission_id, mistakes, hints, seconds, tier, skill_after))

    def performance_history(self, profile_id: int) -> List[Dict[str, Any]]:
        return self._run("SELECT * FROM performance WHERE profile_id=? ORDER BY id", (profile_id,), "all")
