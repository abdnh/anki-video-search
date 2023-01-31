from __future__ import annotations

import json
from typing import Any

from anki import hooks
from anki.collection import Collection
from anki.template import TemplateRenderContext
from aqt import appVersion, gui_hooks, mw
from aqt.browser.previewer import Previewer
from aqt.clayout import CardLayout
from aqt.operations import QueryOp
from aqt.qt import *
from aqt.reviewer import Reviewer
from aqt.utils import openFolder, tooltip
from aqt.webview import WebContent

from . import consts

sys.path.append(str(consts.VENDOR_DIR))

from . import media
from .db import DB

db: DB
anki_version = tuple(int(p) for p in appVersion.split("."))


def configure_folder() -> None:
    folder = QFileDialog.getExistingDirectory(
        mw, caption=f"{consts.ADDON_NAME} - Choose your media folder"
    )
    if not folder:
        return
    media.set_media_folder(folder)
    tooltip("Media folder configured")
    rebuild_db()


def open_folder() -> None:
    openFolder(str(consts.MEDIA_PATH))


def rebuild_db() -> None:
    def op(col: Collection) -> None:
        db.rebuild()

    def on_success(_: Any) -> None:
        tooltip("Database rebuilt")

    query_op = QueryOp(parent=mw, op=op, success=on_success)
    if anki_version >= (2, 1, 50):
        query_op = query_op.with_progress("Rebuilding database...")
    query_op.run_in_background()


def add_field_filter(
    field_text: str, field_name: str, filter_name: str, ctx: TemplateRenderContext
) -> str:
    if not filter_name.startswith(consts.FIELD_FILTER):
        return field_text

    ctx.extra_state.setdefault("vsplayer_id", 0)
    player_id = ctx.extra_state["vsplayer_id"]
    ctx.extra_state["vsplayer_id"] += 1
    playlist = [m.to_playlist_entry() for m in media.get_all_media(mw)]

    # TODO: show current video's number and total video count
    return """
        <div class="vs-player-container">
            <a class="vs-playlist-button vs-prev-button" onclick="VSPlayerPrevious(%(id)s)"></a>
            <video
                id="vs-player-%(id)s"
                class="video-js"
                controls
                preload="auto"
>
            </video>
            <a class="vs-playlist-button vs-next-button" onclick="VSPlayerNext(%(id)s)"></a>
            <script>
                VSInitPlayer(%(id)s, %(playlist)s);
            </script>
        </div>
    """ % dict(
        id=player_id,
        playlist=json.dumps(playlist),
    )


def inject_web_content(web_content: WebContent, context: object | None) -> None:
    if not isinstance(context, (Reviewer, Previewer, CardLayout)):
        return
    web_base = f"/_addons/{mw.addonManager.addonFromModule(__name__)}/web"
    web_content.js.append(f"{web_base}/player.js")
    web_content.js.append(f"{web_base}/vendor/video.min.js")
    web_content.js.append(f"{web_base}/vendor/videojs-playlist.min.js")

    web_content.css.append(f"{web_base}/player.css")
    web_content.css.append(f"{web_base}/vendor/video-js.min.css")


menu = QMenu(consts.ADDON_NAME)
action1 = QAction("Open media folder")
qconnect(action1.triggered, open_folder)
menu.addAction(action1)
action2 = QAction("Configure media folder")
qconnect(action2.triggered, configure_folder)
menu.addAction(action2)
action3 = QAction("Rebuild database")
qconnect(action3.triggered, rebuild_db)
menu.addAction(action3)
mw.form.menuTools.addMenu(menu)
mw.addonManager.setWebExports(__name__, r"(user_files/media/.*)|(web/.*)")
hooks.field_filter.append(add_field_filter)
gui_hooks.webview_will_set_content.append(inject_web_content)
db = DB(mw)
