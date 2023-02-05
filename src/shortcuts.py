from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from aqt import mw

CONFIG = mw.addonManager.getConfig(__name__)

if TYPE_CHECKING:
    from aqt.main import MainWindowState


def repeat() -> None:
    """Repeat matched clip of the most recently played video"""
    mw.reviewer.web.eval(
        """
    (() => {
        const player = VSGetCurrentPlayer();
        if(!player) return;
        player.currentTime(player.playlist()[player.playlist.currentIndex()].startTime);
        player.play();
    })();
    """
    )


def previous() -> None:
    mw.reviewer.web.eval(
        """
    (() => {
        const player = VSGetCurrentPlayer();
        if(!player) return;
        player.playlist.currentItem(player.playlist.previousIndex());
        
    })();
    """
    )


def next() -> None:
    mw.reviewer.web.eval(
        """
    (() => {
        const player = VSGetCurrentPlayer();
        if(!player) return;
        player.playlist.currentItem(player.playlist.nextIndex());
    })();
    """
    )


def pause() -> None:
    mw.reviewer.web.eval(
        """
    (() => {
        const player = VSGetCurrentPlayer();
        if(!player) return;
        if(player.paused()) player.play();
        else player.pause();
    })();
    """
    )


def reset_speed() -> None:
    mw.reviewer.web.eval(
        """
    (() => {
        const player = VSGetCurrentPlayer();
        if(!player) return;
        player.playbackRate(1.0);
    })();
    """
    )


def slow_down() -> None:
    mw.reviewer.web.eval(
        """
    (() => {
        const player = VSGetCurrentPlayer();
        if(!player) return;
        player.playbackRate(player.playbackRate() - 0.1);
    })();
    """
    )


def speed_up() -> None:
    mw.reviewer.web.eval(
        """
    (() => {
        const player = VSGetCurrentPlayer();
        if(!player) return;
        player.playbackRate(player.playbackRate() + 0.1);
    })();
    """
    )


def seek(secs: int) -> None:
    mw.reviewer.web.eval(
        """
    (() => {
        const player = VSGetCurrentPlayer();
        if(!player) return;
        player.currentTime(player.currentTime() + %d);
        player.play();
    })();
    """
        % secs
    )


def backward() -> None:
    seek(-5)


def forward() -> None:
    seek(5)


# TODO: also register the shortcuts in the previewer and card layouts screen
playback_shortcuts = [
    (shortcut, globals()[function])
    for function, shortcut in CONFIG["shortcuts"].items()
]


def register_shortcuts(
    state: MainWindowState, shortcuts: list[tuple[str, Callable]]
) -> None:
    if state == "review":
        shortcuts.extend(playback_shortcuts)
