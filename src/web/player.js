let VS_CURRENT_PLAYER_ID;

function VSInitPlayer(id, playlist, autoplay, autopause) {
    const player = videojs(`vs-player-${id}`, {
        playbackRates: [0.5, 1, 1.5, 2],
    });
    player.playlist(playlist);
    player.playlist.autoadvance(0);
    if (autoplay) {
        player.play();
    }
    player.on("playlistitem", () => {
        const playerContainer = document.getElementById(
            `vs-player-container-${id}`
        );
        const statusElement =
            playerContainer.getElementsByClassName("vs-playlist-status")[0];
        statusElement.textContent = `${player.playlist.currentIndex() + 1} of ${
            player.playlist().length
        }`;
        if (player.textTracks()[0]) {
            player.textTracks()[0].mode = "showing";
        }
        // Work around player breaking with some videos when going through the playlist quickly
        setTimeout(() => {
            player.currentTime(
                playlist[player.playlist.currentIndex()].startTime
            );
        }, 250);
    });
    player.on("play", () => {
        VS_CURRENT_PLAYER_ID = id;
    });
    let autopaused = false;
    if (autopause) {
        player.on("timeupdate", () => {
            if (
                !autopaused &&
                player.currentTime() >=
                    playlist[player.playlist.currentIndex()].endTime
            ) {
                player.pause();
                autopaused = true;
            }
        });
    }
}

function VSGetPlayer(id) {
    return videojs(`vs-player-${id}`);
}

function VSGetCurrentPlayer() {
    if (typeof VS_CURRENT_PLAYER_ID === "undefined") return null;
    return VSGetPlayer(VS_CURRENT_PLAYER_ID);
}

function VSPlayerNext(id) {
    const player = VSGetPlayer(id);
    player.playlist.next();
}

function VSPlayerPrevious(id) {
    const player = VSGetPlayer(id);
    player.playlist.previous();
}
