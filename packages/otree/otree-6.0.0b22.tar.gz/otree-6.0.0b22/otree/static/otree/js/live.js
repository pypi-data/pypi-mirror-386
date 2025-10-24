function makeLiveSocket() {
    var $currentScript = $('#otree-live');
    var socketUrl = $currentScript.data('socketUrl');
    return makeReconnectingWebSocket(socketUrl);
}

var liveSocket = makeLiveSocket();

liveSocket.onmessage = function (e) {
    var data = JSON.parse(e.data);
    if (data.otree_success === false) {
        console.error("Error occurred on the server. See server logs for details.");
        return;
    }

    if (liveRecv !== undefined) {
        liveRecv(data.live_method_payload);
    }
};

function liveSend(msg) {
    liveSocket.send(JSON.stringify(msg));
}

// prevent form submission when user presses enter in an input
$(document).ready(function () {
    $('input').on('keypress', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
        }
    });
});
