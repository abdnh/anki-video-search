from __future__ import annotations

import datetime
import mimetypes
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import webvtt

try:
    from anki.utils import is_win
except ImportError:
    from anki.utils import isWin as is_win

from aqt.main import AnkiQt

from . import consts


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

    def __init__(self, path: Path, web_base: str) -> None:
        self.path = path
        self.web_base = web_base
        # TODO: more sophisticated subtitle matching
        self.subtitles = []
        vtt_sub = path.with_suffix(".vtt")
        if vtt_sub.exists():
            self.subtitles.append(vtt_sub)

    def to_playlist_entry(self) -> dict:
        """Convert to the JSON structure expected by videojs-playlist"""

        sources = [
            {
                "src": self.web_base + self.path.name,
                "type": mimetypes.guess_type(self.path.as_uri())[0],
            }
        ]
        text_tracks = []
        for subtitle in self.subtitles:
            text_tracks.append(
                {
                    "src": self.web_base + subtitle.name,
                    "kind": "captions",
                    "srclang": "en",
                    "label": "English",
                }
            )
        return {"sources": sources, "textTracks": text_tracks}


@dataclass
class Subtitle:
    text: str
    start: datetime.time
    end: datetime.time
    video: str


def get_all_media(mw: AnkiQt | None = None) -> list[Media]:
    media_list = []
    web_base = ""
    if mw:
        web_base = f"/_addons/{mw.addonManager.addonFromModule(__name__)}/user_files/{consts.MEDIA_PATH.name}/"
    # TODO: support more formats
    for path in consts.MEDIA_PATH.glob("*.webm"):
        media_list.append(Media(path, web_base))
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
                        media.path.name,
                    )
                )
    return subtitles
