function VSInitPlayer(id, playlist) {
    const player = videojs(`vs-player-${id}`, {
        playbackRates: [0.5, 1, 1.5, 2],
    });
    player.playlist(playlist);
    player.playlist.autoadvance(0);
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
