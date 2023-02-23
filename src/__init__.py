from __future__ import annotations

import json
from typing import Any

from anki import hooks
from anki.cards import Card
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
from .shortcuts import register_shortcuts
from .utils import time_to_seconds

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
    return v.lower() != "false"


def get_filter_int_option(options: dict[str, str], key: str) -> int:
    v = options.get(key, None)
    if not v:
        return 0
    try:
        return int(v)
    except ValueError:
        return 0


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
    autopause = get_filter_bool_option(options, "autopause", True)
    delay = get_filter_int_option(options, "delay")
    playlist = []
    for m in media.get_matching_media(mw, db, field_text):
        m.start -= delay
        playlist.append(m.to_playlist_entry())

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
                <div class="vs-playlist-status"></div>
                <div class="vs-vid-panel-container">
                    <video
                        id="vs-player-%(id)s"
                        class="video-js"
                        controls
                        preload="auto"
                    ></video>
                    <div class="vs-subs-panel"></div>
                </div>
                <div class="vs-current-sub"></div>
            </div>
            <a
                class="vs-playlist-button vs-next-button"
                onclick="VSPlayerNext(%(id)s)"
            ></a>
            <script>
                VSInitPlayer(%(id)s, %(playlist)s, %(text)s, %(autoplay)d, %(autopause)d);
            </script>
        </div>
    """ % dict(
        id=player_id,
        playlist=json.dumps(playlist),
        text=json.dumps(field_text),
        autoplay=autoplay,
        autopause=autopause,
    )


def inject_web_content(web_content: WebContent, context: object | None) -> None:
    if not isinstance(context, (Reviewer, Previewer, CardLayout)):
        return
    web_base = f"/_addons/{mw.addonManager.addonFromModule(__name__)}/web"
    web_content.js.append(f"{web_base}/player.js")
    web_content.js.append(f"{web_base}/vendor/video.min.js")
    web_content.js.append(f"{web_base}/vendor/videojs-playlist.min.js")

    web_content.css.append(f"{web_base}/vendor/video-js.min.css")
    web_content.css.append(f"{web_base}/player.css")


def on_card_will_show(text: str, card: Card, kind: str) -> str:
    text = (
        """\
    <script>
        for(const player of videojs.getAllPlayers()) {
            player.dispose();
        }
    </script>
    """
        + text
    )
    return text


def handle_js_msg(
    handled: tuple[bool, Any], message: str, context: Any
) -> tuple[bool, Any]:
    if not message.startswith("vs-subs:"):
        return handled
    file = message.split(":", maxsplit=1)[1].split("/")[-1]
    subs = media.get_media_sub(file)
    data = []
    for sub in subs:
        data.append(
            {
                "text": sub.text,
                "start": time_to_seconds(sub.start),
                "end": time_to_seconds(sub.end),
            }
        )

    return (True, data)


def accept_fullscreen_request(request: QWebEngineFullScreenRequest) -> None:
    request.accept()


def enable_fullscreen() -> None:
    mw.reviewer.web.settings().setAttribute(
        QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True
    )
    qconnect(mw.reviewer.web.page().fullScreenRequested, accept_fullscreen_request)


def add_menu() -> None:
    menu = QMenu(consts.ADDON_NAME, mw)
    action1 = QAction("Open media folder", menu)
    qconnect(action1.triggered, open_folder)
    menu.addAction(action1)
    action2 = QAction("Configure media folder", menu)
    qconnect(action2.triggered, configure_folder)
    menu.addAction(action2)
    action3 = QAction("Rebuild database", menu)
    qconnect(action3.triggered, rebuild_db)
    menu.addAction(action3)
    mw.form.menuTools.addMenu(menu)


def register_hooks() -> None:
    mw.addonManager.setWebExports(__name__, r"(user_files/media/.*)|(web/.*)")
    hooks.field_filter.append(add_field_filter)
    gui_hooks.webview_will_set_content.append(inject_web_content)
    gui_hooks.state_shortcuts_will_change.append(register_shortcuts)
    gui_hooks.card_will_show.append(on_card_will_show)
    gui_hooks.webview_did_receive_js_message.append(handle_js_msg)


db = DB(mw)
add_menu()
register_hooks()
enable_fullscreen()
