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
        db.rebuild(media.get_all_subs())

    def on_success(_: Any) -> None:
        tooltip("Database rebuilt")

    query_op = QueryOp(parent=mw, op=op, success=on_success)
    if anki_version >= (2, 1, 50):
        query_op = query_op.with_progress("Rebuilding database...")
    query_op.run_in_background()


def get_filter_bool_option(
    options: dict[str, str], key: str, default: bool = False
) -> bool:
    v = options.get(key, None)
    if not v:
        return default
    return v != "False"


def add_field_filter(
    field_text: str, field_name: str, filter_name: str, ctx: TemplateRenderContext
) -> str:
    if not filter_name.startswith(consts.FIELD_FILTER):
        return field_text

    ctx.extra_state.setdefault("vsplayer_id", 0)
    player_id = ctx.extra_state["vsplayer_id"]
    ctx.extra_state["vsplayer_id"] += 1

    options = {}
    for opt in filter_name.split()[1:]:
        p = opt.split("=")
        if len(p) > 1:
            options[p[0]] = p[1]
        else:
            options[p[0]] = "True"

    autoplay = get_filter_bool_option(options, "autoplay")
    playlist = [
        m.to_playlist_entry() for m in media.get_matching_media(mw, db, field_text)
    ]

    if not playlist:
        return (
            "<div style='color: red'>No videos matching '%s' were found.</div>"
            % field_text
        )

    return """
        <div class="vs-player-container" id="vs-player-container-%(id)s">
            <a
                class="vs-playlist-button vs-prev-button"
                onclick="VSPlayerPrevious(%(id)s)"
            ></a>
            <div class="vs-player-main-view">
                <video
                    id="vs-player-%(id)s"
                    class="video-js"
                    controls
                    preload="auto"
                ></video>
                <div class="vs-playlist-status"></div>
            </div>
            <a
                class="vs-playlist-button vs-next-button"
                onclick="VSPlayerNext(%(id)s)"
            ></a>
            <script>
                VSInitPlayer(%(id)s, %(playlist)s, %(autoplay)d);
            </script>
        </div>
    """ % dict(
        id=player_id,
        playlist=json.dumps(playlist),
        autoplay=autoplay,
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
