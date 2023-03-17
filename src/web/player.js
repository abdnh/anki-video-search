let VS_CURRENT_PLAYER_ID;
let VS_PLAYBACKRATE = 1;

function _VSInitPlayer(id, playlist, searchText, autoplay, autopause) {
    const playerContainer = document.getElementById(
        `vs-player-container-${id}`
    );
    const statusElement =
        playerContainer.getElementsByClassName("vs-playlist-status")[0];
    const subsPanel = playerContainer.querySelector(".vs-subs-panel");
    const currentSubContainer =
        playerContainer.querySelector(".vs-current-sub");
    if (!playlist || !playlist.length) {
        playerContainer.previousElementSibling.style.display = "none";
        const errorElement = document.createElement("div");
        errorElement.classList.add("vs-nomatch");
        errorElement.textContent = `No videos matching '${searchText}' were found`;
        playerContainer.insertAdjacentElement("afterend", errorElement);
        return;
    }

    const player = videojs(`vs-player-${id}`, {
        playbackRates: [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2],
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
        statusElement.textContent = `${player.playlist.currentIndex() + 1} of ${
            player.playlist().length
        }`;

        setTimeout(() => {
            if (player.playlist.currentIndex() === 0) {
                playerContainer.previousElementSibling.style.display = "none";
                playerContainer.style.removeProperty("display");
            }

            const textTrack = player.textTracks()[0];
            pycmd(
                `video-search:${JSON.stringify({
                    name: "subs",
                    file: player.src(),
                })}`,
                (subs) => {
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
                                oldSubElement.classList.remove(
                                    "vs-panel-current-sub"
                                );
                            }
                            subElement.classList.add("vs-panel-current-sub");
                            subElement.scrollIntoView();
                        });
                    }
                }
            );

            player.currentTime(
                playlist[player.playlist.currentIndex()].startTime
            );
            player.playbackRate(VS_PLAYBACKRATE);
        }, 100);
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

function VSInitPlayer(id, playlist, searchText, autoplay, autopause) {
    // Wait for the player container to be available.
    // This is needed because Anki renders both card sides's field filters before showing the card,
    // so we may end up trying to initialize the player before it's placed in the DOM
    const intervalId = setInterval(() => {
        const playerContainer = document.getElementById(
            `vs-player-container-${id}`
        );
        if (playerContainer) {
            clearInterval(intervalId);
            _VSInitPlayer(id, playlist, searchText, autoplay, autopause);
        }
    }, 50);
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
    VS_PLAYBACKRATE = player.playbackRate();
    player.playlist.next();
}

function VSPlayerPrevious(id) {
    const player = VSGetPlayer(id);
    VS_PLAYBACKRATE = player.playbackRate();
    player.playlist.previous();
}
