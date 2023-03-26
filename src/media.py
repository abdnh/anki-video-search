from __future__ import annotations

import datetime
import glob
import mimetypes
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

import webvtt

try:
    from anki.utils import is_win
except ImportError:
    from anki.utils import isWin as is_win

from aqt.main import AnkiQt

from . import consts
from .db import DB


def set_media_folder(path: str | Path) -> None:
    if consts.MEDIA_PATH.exists():
        consts.MEDIA_PATH.rmdir()
    if is_win:
        subprocess.run(
            'mklink /J "{}" "{}"'.format(str(consts.MEDIA_PATH), str(path)),
            check=True,
            shell=True,
        )
    else:
        os.link(path, consts.MEDIA_PATH)


class Media:
    path: Path
    subtitles: list[Path]

    def __init__(
        self, path: Path, web_base: str = "", start: float = 0, end: float = 0
    ) -> None:
        self.path = path
        self.web_base = web_base
        self.start = start
        self.end = end
        self.subtitles = []
        for sub_path in consts.MEDIA_PATH.rglob(f"*{glob.escape(path.stem)}*.vtt"):
            self.subtitles.append(sub_path)

    def to_playlist_entry(self) -> dict:
        """Convert to the JSON structure expected by videojs-playlist"""
        sources = [
            {
                "src": self.web_base + str(self.path.relative_to(consts.MEDIA_PATH)),
                "type": mimetypes.guess_type(self.path.as_uri())[0],
            }
        ]
        text_tracks = []
        for subtitle in self.subtitles:
            text_tracks.append(
                {
                    "src": self.web_base + str(subtitle.relative_to(consts.MEDIA_PATH)),
                    "kind": "captions",
                    "srclang": "en",
                    "label": "English",
                }
            )
        return {
            "sources": sources,
            "textTracks": text_tracks,
            "startTime": self.start,
            "endTime": self.end,
        }


@dataclass
class Subtitle:
    text: str
    start: datetime.time
    end: datetime.time
    video: str


def get_all_media() -> list[Media]:
    media_list = []
    # TODO: support more formats
    for path in consts.MEDIA_PATH.rglob("*.webm"):
        media_list.append(Media(path))
    return media_list


def get_matching_media(mw: AnkiQt, db: DB, text: str) -> list[Media]:
    media_list = []
    web_base = f"/_addons/{mw.addonManager.addonFromModule(__name__)}/user_files/{consts.MEDIA_PATH.name}/"
    for video, start, end in db.search(text):
        media_list.append(Media(consts.MEDIA_PATH / video, web_base, start, end))
    return media_list


def parse_webvtt_timestamp(timestamp: str) -> datetime.time:
    return datetime.datetime.strptime(timestamp, "%H:%M:%S.%f").time()


def get_all_subs() -> list[Subtitle]:
    subtitles = []
    media_list = get_all_media()
    for media in media_list:
        for subtitle_file in media.subtitles:
            for caption in webvtt.read(subtitle_file):
                subtitles.append(
                    Subtitle(
                        caption.text,
                        parse_webvtt_timestamp(caption.start),
                        parse_webvtt_timestamp(caption.end),
                        str(media.path.relative_to(consts.MEDIA_PATH)),
                    )
                )
    return subtitles


def get_media_sub(media_file: str) -> Generator[Subtitle, None, None]:
    media = Media(consts.MEDIA_PATH / media_file)
    if not media.subtitles:
        return

    subtitle_file = media.subtitles[0]
    for caption in webvtt.read(subtitle_file):
        yield Subtitle(
            caption.text,
            parse_webvtt_timestamp(caption.start),
            parse_webvtt_timestamp(caption.end),
            media.path.name,
        )
