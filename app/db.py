from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Literal, Optional

import aiosqlite

SettingKey = Literal["welcome_message", "sale_message", "channel_url"]


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


DEFAULT_SETTINGS: dict[SettingKey, str] = {
    "welcome_message": "Привет, это шаблон сообщения.",
    "sale_message": "Покупайте курс.",
    "channel_url": "https://t.me/",
}


@dataclass
class UserRow:
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    created_at: str
    current_question: int
    answers: str
    count_a: int
    count_b: int
    count_c: int
    count_d: int
    result_type: Optional[str]
    completed_at: Optional[str]
    clicked_buy: int
    clicked_channel: int


class Database:
    def __init__(self, path: str) -> None:
        self.path = path

    async def connect(self) -> aiosqlite.Connection:
        conn = await aiosqlite.connect(self.path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON;")
        await conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    async def init(self) -> None:
        async with await self.connect() as db:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    created_at TEXT NOT NULL,
                    current_question INTEGER NOT NULL DEFAULT 0,
                    answers TEXT NOT NULL DEFAULT '[]',
                    count_a INTEGER NOT NULL DEFAULT 0,
                    count_b INTEGER NOT NULL DEFAULT 0,
                    count_c INTEGER NOT NULL DEFAULT 0,
                    count_d INTEGER NOT NULL DEFAULT 0,
                    result_type TEXT,
                    completed_at TEXT,
                    clicked_buy INTEGER NOT NULL DEFAULT 0,
                    clicked_channel INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
                CREATE INDEX IF NOT EXISTS idx_users_completed ON users(completed_at);
                """
            )
            for k, v in DEFAULT_SETTINGS.items():
                await db.execute(
                    """
                    INSERT INTO settings(key, value, updated_at)
                    VALUES(?, ?, ?)
                    ON CONFLICT(key) DO NOTHING;
                    """,
                    (k, v, utcnow_iso()),
                )
            await db.commit()

    async def upsert_user(self, user_id: int, username: Optional[str], first_name: Optional[str]) -> None:
        async with await self.connect() as db:
            await db.execute(
                """
                INSERT INTO users(user_id, username, first_name, created_at)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                  username=excluded.username,
                  first_name=excluded.first_name;
                """,
                (user_id, username, first_name, utcnow_iso()),
            )
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[UserRow]:
        async with await self.connect() as db:
            cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            return UserRow(**dict(row)) if row else None

    async def reset_session(self, user_id: int) -> None:
        async with await self.connect() as db:
            await db.execute(
                """
                UPDATE users
                SET current_question=0,
                    answers='[]',
                    count_a=0, count_b=0, count_c=0, count_d=0,
                    result_type=NULL,
                    completed_at=NULL,
                    clicked_buy=0,
                    clicked_channel=0
                WHERE user_id=?;
                """,
                (user_id,),
            )
            await db.commit()

    async def append_answer(self, user_id: int, letter: str) -> None:
        async with await self.connect() as db:
            cur = await db.execute("SELECT answers, count_a, count_b, count_c, count_d, current_question FROM users WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            if not row:
                raise RuntimeError("User not found")

            answers = json.loads(row["answers"])
            answers.append(letter)

            counts = {
                "A": int(row["count_a"]),
                "B": int(row["count_b"]),
                "C": int(row["count_c"]),
                "D": int(row["count_d"]),
            }
            if letter not in counts:
                raise ValueError("Invalid letter")
            counts[letter] += 1

            await db.execute(
                """
                UPDATE users
                SET answers=?,
                    count_a=?, count_b=?, count_c=?, count_d=?,
                    current_question=?
                WHERE user_id=?;
                """,
                (
                    json.dumps(answers, ensure_ascii=False),
                    counts["A"],
                    counts["B"],
                    counts["C"],
                    counts["D"],
                    int(row["current_question"]) + 1,
                    user_id,
                ),
            )
            await db.commit()

    async def set_completed(self, user_id: int, result_type: str) -> None:
        async with await self.connect() as db:
            await db.execute(
                "UPDATE users SET result_type=?, completed_at=? WHERE user_id=?",
                (result_type, utcnow_iso(), user_id),
            )
            await db.commit()

    async def get_setting(self, key: SettingKey) -> str:
        async with await self.connect() as db:
            cur = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = await cur.fetchone()
            if not row:
                return DEFAULT_SETTINGS[key]
            return str(row["value"])

    async def set_setting(self, key: SettingKey, value: str) -> None:
        async with await self.connect() as db:
            await db.execute(
                """
                INSERT INTO settings(key, value, updated_at)
                VALUES(?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                  value=excluded.value,
                  updated_at=excluded.updated_at;
                """,
                (key, value, utcnow_iso()),
            )
            await db.commit()

    async def add_event(self, user_id: int, event_type: str) -> None:
        async with await self.connect() as db:
            await db.execute(
                "INSERT INTO events(user_id, event_type, created_at) VALUES(?, ?, ?)",
                (user_id, event_type, utcnow_iso()),
            )
            await db.commit()

    async def set_clicked_buy(self, user_id: int) -> None:
        async with await self.connect() as db:
            await db.execute("UPDATE users SET clicked_buy=1 WHERE user_id=?", (user_id,))
            await db.commit()

    async def set_clicked_channel(self, user_id: int) -> None:
        async with await self.connect() as db:
            await db.execute("UPDATE users SET clicked_channel=1 WHERE user_id=?", (user_id,))
            await db.commit()

    async def stats(self) -> dict[str, Any]:
        async with await self.connect() as db:
            out: dict[str, Any] = {}
            cur = await db.execute("SELECT COUNT(*) AS c FROM users")
            out["users_total"] = int((await cur.fetchone())["c"])

            cur = await db.execute("SELECT COUNT(*) AS c FROM users WHERE completed_at IS NOT NULL")
            out["completed_total"] = int((await cur.fetchone())["c"])

            cur = await db.execute(
                """
                SELECT result_type, COUNT(*) AS c
                FROM users
                WHERE completed_at IS NOT NULL AND result_type IS NOT NULL
                GROUP BY result_type
                """
            )
            out["by_type"] = {str(r["result_type"]): int(r["c"]) for r in await cur.fetchall()}

            cur = await db.execute("SELECT COUNT(*) AS c FROM users WHERE clicked_buy=1")
            out["clicked_buy_total"] = int((await cur.fetchone())["c"])

            cur = await db.execute("SELECT COUNT(*) AS c FROM users WHERE clicked_channel=1")
            out["clicked_channel_total"] = int((await cur.fetchone())["c"])

            return out

    async def export_users_csv(self) -> str:
        # Returns CSV text (UTF-8), caller can send as document.
        async with await self.connect() as db:
            cur = await db.execute(
                """
                SELECT user_id, username, first_name, created_at, completed_at, result_type
                FROM users
                ORDER BY created_at DESC
                """
            )
            rows = await cur.fetchall()

        def esc(v: Any) -> str:
            if v is None:
                return ""
            s = str(v)
            if any(ch in s for ch in [",", '"', "\n", "\r"]):
                s = '"' + s.replace('"', '""') + '"'
            return s

        header = "user_id,username,first_name,created_at,completed_at,result_type"
        lines = [header]
        for r in rows:
            lines.append(
                ",".join(
                    [
                        esc(r["user_id"]),
                        esc(r["username"]),
                        esc(r["first_name"]),
                        esc(r["created_at"]),
                        esc(r["completed_at"]),
                        esc(r["result_type"]),
                    ]
                )
            )
        return "\n".join(lines) + "\n"

