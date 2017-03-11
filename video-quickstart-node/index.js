/*
 Load Twilio configuration from .env config file - the following environment
 variables should be set:
 process.env.TWILIO_ACCOUNT_SID
 process.env.TWILIO_API_KEY
 process.env.TWILIO_API_SECRET
 process.env.TWILIO_CONFIGURATION_SID
 */
require('dotenv').load();
const uuidV4 = require('uuid/v4');

var http = require('http');
var path = require('path');
var AccessToken = require('twilio').AccessToken;
var VideoGrant = AccessToken.VideoGrant;
var express = require('express');
var randomUsername = require('./randos');

var Parse = require('parse/node');

Parse.initialize("DotaMate","abc123","Shaman10201");
Parse.serverURL = 'http://95.85.22.29:80/parse';

var VoiceRecording = Parse.Object.extend("VoiceRecording");


// Create Express webapp
var bodyParser = require("body-parser");
var app = express();
app.use('/public', express.static(__dirname + '/public'));
app.use(express.static(__dirname + '/public'));

//Here we are configuring express to use body-parser as middle-ware.
app.use(bodyParser.urlencoded({extended: false, limit: '500mb'}));
app.use(bodyParser.json({limit: '500mb'}));

/*
 Generate an Access Token for a chat application user - it generates a random
 username for the client requesting a token, and takes a device ID as a query
 parameter.
 */
app.get('/token', function (request, response) {
    var identity = randomUsername();

    // Create an access token which we will sign and return to the client,
    // containing the grant we just created
    var token = new AccessToken(
        process.env.TWILIO_ACCOUNT_SID,
        process.env.TWILIO_API_KEY,
        process.env.TWILIO_API_SECRET
    );

    // Assign the generated identity to the token
    token.identity = identity;
    token.conversationId = uuidV4();

    //grant the access token Twilio Video capabilities
    var grant = new VideoGrant();
    grant.configurationProfileSid = process.env.TWILIO_CONFIGURATION_SID;
    token.addGrant(grant);

    // Serialize the token to a JWT string and include it in a JSON response
    response.send({
        identity: identity,
        token: token.toJwt()
    });
});

var fs = require('fs');
app.post('/save_recording', function (req, res) {
    var fileName = uuidV4() + '.wav';
    var voiceRecording = new VoiceRecording();
    voiceRecording.set("sessionId", req.body.conversationId);
    voiceRecording.set("data", new Parse.File( fileName,{ base64: req.body.blob } , "wav" ) );
    voiceRecording.set("startDateTimeStamp" , new Date(req.body.startRecordDate));

    voiceRecording.save(null, {
        success: function (data) {
            // Execute any logic that should take place after the object is saved.
            console.log('New object created with objectId: ' + data.id);
            return res.json({'status': 'success'});
        },
        error: function (gameScore, error) {
            // Execute any logic that should take place if the save fails.
            // error is a Parse.Error with an error code and message.
            console.log('Failed to create new object, with error code: ' + error.message);
        }
    });

});

// Create http server and run it
var server = http.createServer(app);
var port = process.env.PORT || 3000;
server.listen(port, function () {
    console.log('Express server running on *:' + port);
});
