import datetime
import sqlite3

from aqt.main import AnkiQt

from . import consts, media


def time_to_seconds(time: datetime.time) -> float:
    return (
        time.hour * 3600 + time.minute * 60 + time.second + time.microsecond / 1000000
    )


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

    def rebuild(self) -> None:
        values = []
        self.conn.execute("DELETE FROM subtitles")
        for subtitle in media.get_all_subs():
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
                "INSERT INTO subtitles(text, start, end, video) VALUES (?, ?, ?, ?)",
                values,
            )
