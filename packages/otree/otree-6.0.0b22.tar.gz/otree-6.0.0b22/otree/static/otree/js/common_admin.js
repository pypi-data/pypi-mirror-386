function makeReconnectingWebSocket(path) {
    // https://github.com/pladaria/reconnecting-websocket/issues/91#issuecomment-431244323
    var ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
    var ws_path = ws_scheme + '://' + window.location.host + path;
    var socket = new ReconnectingWebSocket(ws_path);
    var serverErrorDiv = document.getElementById("websocket-server-error");

    socket.addEventListener('close', function (e) {
        // this may or may not exist in child pages.
        // we need this so that if someone's trying to create a session or export data,
        // they get a notification of why it isn't working, rather than staring at the spinner
        // forever.
        if (serverErrorDiv) {
            // better to put the message here rather than the div, otherwise it's confusing when
            // you do "view source" and there's an error message.
            if (e.code === 1011) {
                serverErrorDiv.innerText = "Server error. Check the server logs or Sentry.";
            } else {
                serverErrorDiv.innerText = "Connection to server lost.";
            }
            serverErrorDiv.style.visibility = "visible";
        }
    });

    socket.addEventListener('open', function(e) {
        serverErrorDiv.style.visibility = "hidden";
    });

    return socket;
}
