from __future__ import annotations

from aqt import mw
from aqt.qt import *
from aqt.utils import openFolder, tooltip

from . import consts, media


def configure_folder() -> None:
    folder = QFileDialog.getExistingDirectory(
        mw, caption=f"{consts.ADDON_NAME} - Choose your media folder"
    )
    if not folder:
        return
    media.set_media_folder(folder)
    tooltip("Media folder configured")


def open_folder() -> None:
    openFolder(str(consts.MEDIA_PATH))


menu = QMenu(consts.ADDON_NAME)
action1 = QAction("Open media folder")
qconnect(action1.triggered, open_folder)
menu.addAction(action1)
action2 = QAction("Configure media folder")
qconnect(action2.triggered, configure_folder)
menu.addAction(action2)
mw.form.menuTools.addMenu(menu)
mw.addonManager.setWebExports(__name__, r"user_files/media/.*")
