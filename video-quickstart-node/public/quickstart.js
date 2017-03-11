var videoClient;
var activeRoom;
var previewMedia;
var identity;
var roomName;

// Check for WebRTC
if (!navigator.webkitGetUserMedia && !navigator.mozGetUserMedia) {
    alert('WebRTC is not available in your browser.');
}

// When we are about to transition away from this page, disconnect
// from the room, if joined.
window.addEventListener('beforeunload', leaveRoomIfJoined);

var conversationId;
$.getJSON('/token', function (data) {
    identity = data.identity;
    // Create a Video Client and connect to Twilio
    videoClient = new Twilio.Video.Client(data.token);
    document.getElementById('room-controls').style.display = 'block';

    // Bind button to join room
    document.getElementById('button-join').onclick = function () {
        roomName = document.getElementById('room-name').value;
        if (roomName) {
            log("Joining room '" + roomName + "'...");

            videoClient.connect({to: roomName}).then(roomJoined,
                function (error) {
                    log('Could not connect to Twilio: ' + error.message);
                });
        } else {
            alert('Please enter a room name.');
        }
    };

    // Bind button to leave room
    document.getElementById('button-leave').onclick = function () {
        log('Leaving room...');
        activeRoom.disconnect();
    };
});

var mediaRecorder;
var ourFirstParticipant = true;
var blob;

function startRecordingClientAudio() {
    navigator.getUserMedia =
        ( navigator.getUserMedia ||
        navigator.webkitGetUserMedia ||
        navigator.mozGetUserMedia ||
        navigator.msGetUserMedia);

    var audioCtx = new (window.AudioContext || webkitAudioContext)();
    if (navigator.getUserMedia) {
        console.log('getUserMedia supported.');

        var constraints = {audio: true};
        var chunks = [];

        var onSuccess = function(stream) {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            console.log(mediaRecorder.state);
            console.log("recorder started");

            mediaRecorder.ondataavailable = function (e) {
                chunks.push(e.data);
            };

            mediaRecorder.onstop = function (e) {
                console.log("data available after MediaRecorder.stop() called.");
                blob = new Blob(chunks, {'type': 'audio/ogg; codecs=opus'});
                chunks = [];
                blobToBase64(blob);
            };
        };

        var onError = function(err) {
            console.log('The following error occured: ' + err);
        };

        navigator.getUserMedia(constraints, onSuccess, onError);
    } else {
        console.log('getUserMedia not supported on your browser!');
    }
}

//Send blob to api
function sendToApi(base64) { // encode
    var update = {'blob': base64, 'identifier': conversationId};

    $.ajax({
        type: "POST",
        url: '/save_recording',
        data: update,
        success: function (new_recording) {
            console.log("success");
        },
        dataType: 'application/json'
    });
}

// converts blob to base64
var blobToBase64 = function (blob) {
    var reader = new FileReader();
    reader.onload = function () {
        var dataUrl = reader.result;
        var base64 = dataUrl.split(',')[1];
        sendToApi(base64);
    };
    reader.readAsDataURL(blob);
};

// Successfully connected!
function roomJoined(room) {
    activeRoom = room;
    conversationId = activeRoom.sid;

    log("Joined as '" + identity + "'");
    document.getElementById('button-join').style.display = 'none';
    document.getElementById('button-leave').style.display = 'inline';

    // Draw local video, if not already previewing
    if (!previewMedia) {
        room.localParticipant.media.attach('#local-media');
    }

    function onData(data) {
        if (data.end) streamer.end();
        else streamer.append(data);
    }


    room.participants.forEach(function (participant) {
        log("Already in Room: '" + participant.identity + "'");

        participant.media.attach('#remote-media');
    });

    // When a participant joins, draw their video on screen
    room.on('participantConnected', function (participant) {
        log("Joining: '" + participant.identity + "'");
        participant.media.attach('#remote-media');
        if (ourFirstParticipant) {
            startRecordingClientAudio();
            ourFirstParticipant = false;
        }

    });

    // When a participant disconnects, note in log
    room.on('participantDisconnected', function (participant) {
        log("Participant '" + participant.identity + "' left the room");
        participant.media.detach();
        mediaRecorder.stop();
    });

    // When we are disconnected, stop capturing local video
    // Also remove media for all remote participants
    room.on('disconnected', function () {
        log('Left');
        room.localParticipant.media.detach();
        room.participants.forEach(function (participant) {
            participant.media.detach();
        });
        activeRoom = null;
        document.getElementById('button-join').style.display = 'inline';
        document.getElementById('button-leave').style.display = 'none';
    });
}

//  Local video preview
document.getElementById('button-preview').onclick = function () {
    if (!previewMedia) {
        previewMedia = new Twilio.Video.LocalMedia();
        Twilio.Video.getUserMedia().then(
            function (mediaStream) {
                previewMedia.addStream(mediaStream);
                previewMedia.attach('#local-media');
            },
            function (error) {
                console.error('Unable to access local media', error);
                log('Unable to access Camera and Microphone');
            });
    }
};

// Activity log
function log(message) {
    var logDiv = document.getElementById('log');
    logDiv.innerHTML += '<p>&gt;&nbsp;' + message + '</p>';
    logDiv.scrollTop = logDiv.scrollHeight;
}

function leaveRoomIfJoined() {
    if (activeRoom) {
        activeRoom.disconnect();
    }
}
