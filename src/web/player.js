let VS_CURRENT_PLAYER_ID;

function VSInitPlayer(id, playlist, searchText, autoplay, autopause) {
    const player = videojs(`vs-player-${id}`, {
        playbackRates: [0.5, 1, 1.5, 2],
    });
    player.playlist(playlist);
    player.playlist.autoadvance(0);
    if (autoplay) {
        player.play();
    }
    // Escape all special regex characters except *, which is interpreted as ".*"
    searchText = searchText
        .replace(/[.+?^${}()|[\]\\]/g, "\\$&")
        .replace("*", ".*");
    const searchRegex = new RegExp(searchText, "gi");

    function highlightSub(text) {
        // Escape HTML
        text = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
        text = text.replace(
            searchRegex,
            '<span class="vs-highlight">$&</span>'
        );
        return text;
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
        const subsPanel = playerContainer.querySelector(".vs-subs-panel");
        const currentSubContainer =
            playerContainer.querySelector(".vs-current-sub");

        const textTrack = player.textTracks()[0];
        pycmd(`vs-subs:${player.src()}`, (subs) => {
            subsPanel.innerHTML = "";
            for (let i = 0; i < subs.length; i++) {
                const sub = subs[i];
                const subElement = document.createElement("div");
                subElement.classList.add("vs-panel-sub");
                subElement.innerHTML = highlightSub(sub.text);
                subElement.dataset.start = sub.start;
                subElement.dataset.end = sub.end;
                subsPanel.append(subElement);
                textTrack.cues[i].id = i;
                subElement.addEventListener("click", () => {
                    player.currentTime(sub.start);
                });
            }
            if (textTrack) {
                textTrack.mode = "hidden";
                textTrack.addEventListener("cuechange", () => {
                    const cues = Array.from(textTrack.activeCues);
                    const text = cues.map((cue) => cue.text).join("\n");
                    currentSubContainer.innerHTML = highlightSub(text);

                    const firstCue = cues[0];
                    const subElement = subsPanel.children[firstCue.id];
                    const oldSubElement = subsPanel.querySelector(
                        ".vs-panel-current-sub"
                    );
                    if (oldSubElement) {
                        oldSubElement.classList.remove("vs-panel-current-sub");
                    }
                    subElement.classList.add("vs-panel-current-sub");
                    subElement.scrollIntoView();
                });
            }
        });

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
