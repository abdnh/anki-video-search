from __future__ import annotations

import os
import subprocess
from pathlib import Path

from anki.utils import isWin

from . import consts


def set_media_folder(path: str | Path) -> None:
    if consts.MEDIA_PATH.exists():
        consts.MEDIA_PATH.rmdir()
    if isWin:
        subprocess.run(
            'mklink /J "{}" "{}"'.format(str(consts.MEDIA_PATH), str(path)),
            check=True,
            shell=True,
        )
    else:
        os.link(path, consts.MEDIA_PATH)
