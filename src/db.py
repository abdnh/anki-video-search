from __future__ import annotations

import datetime
import sqlite3
from typing import TYPE_CHECKING

from aqt.main import AnkiQt

from . import consts

if TYPE_CHECKING:
    from .media import Subtitle


def time_to_seconds(time: datetime.time) -> float:
    return (
        time.hour * 3600 + time.minute * 60 + time.second + time.microsecond / 1000000
    )


def escape_search(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = text.replace("%", "\\%")
    text = text.replace("_", "\\_")
    # Treat * as a wildcard
    text = text.replace("*", "%")
    return text


class DB:
    def __init__(self, mw: AnkiQt) -> None:
        self.mw = mw
        self.conn = sqlite3.connect(consts.DB_FILE, check_same_thread=False)
        self._create_if_needed()

    def _create_if_needed(self) -> None:
        self.conn.executescript(
            """
        CREATE TABLE IF NOT EXISTS subtitles (
            text TEXT,
            start INT,
            end INT,
            video TEXT
        );
        """
        )

    def rebuild(self, subtitles: list[Subtitle]) -> None:
        values = []
        self.conn.execute("DELETE FROM subtitles;")
        for subtitle in subtitles:
            values.append(
                (
                    subtitle.text,
                    time_to_seconds(subtitle.start),
                    time_to_seconds(subtitle.end),
                    subtitle.video,
                )
            )
        with self.conn:
            self.conn.executemany(
                "INSERT INTO subtitles(text, start, end, video) VALUES (?, ?, ?, ?);",
                values,
            )

    def search(self, text: str) -> list[tuple[str, int]]:
        text = escape_search(text)
        return self.conn.execute(
            f"SELECT video, start FROM subtitles WHERE text LIKE '%' || ? || '%' ESCAPE '\\' ORDER BY video, start;",
            (text,),
        ).fetchall()
