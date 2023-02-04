function VSInitPlayer(id, playlist) {
    const player = videojs(`vs-player-${id}`, {
        playbackRates: [0.5, 1, 1.5, 2],
    });
    player.playlist(playlist);
    player.playlist.autoadvance(0);
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
        player.currentTime(playlist[player.playlist.currentIndex()].startTime);
    });
}

function VSGetPlayer(id) {
    return videojs(`vs-player-${id}`);
}

function VSPlayerNext(id) {
    const player = VSGetPlayer(id);
    player.playlist.next();
}

function VSPlayerPrevious(id) {
    const player = VSGetPlayer(id);
    player.playlist.previous();
}
