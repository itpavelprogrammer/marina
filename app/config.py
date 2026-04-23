from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


def _parse_admin_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for part in (raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        ids.add(int(part))
    return ids


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: set[int]
    db_path: str
    parse_mode: str
    question_delay_sec: float


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is required (set it in .env)")

    admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    db_path = os.getenv("DB_PATH", "bot.db").strip() or "bot.db"
    parse_mode = (os.getenv("PARSE_MODE", "HTML") or "HTML").strip()
    question_delay_sec = float(os.getenv("QUESTION_DELAY_SEC", "0") or "0")

    return Config(
        bot_token=bot_token,
        admin_ids=admin_ids,
        db_path=db_path,
        parse_mode=parse_mode,
        question_delay_sec=question_delay_sec,
    )

