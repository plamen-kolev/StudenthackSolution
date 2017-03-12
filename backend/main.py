import os
os.environ["PARSE_API_ROOT"] = "http://95.85.22.29/parse"

# Everything else same as usual
import pdb
from configuration import configure
from parse_rest.datatypes import Object
from parse_rest.connection import register
from parse_rest.user import User    
from math import log
import urllib2
import numpy as np
from flask import Flask, request  
import wave
from subprocess import call
from base64 import decodestring
from audio_transcribe import recognize
import json

configure()

app = Flask(__name__)
recFilename = 'voice_tmp'

keyWordStore = {}

@app.route("/calculate", methods = ['POST'])
def calculate():
    
    if request.method == 'POST':
        sessionId = request.form["sessionId"]
        wave_classname = "Wave"
        waves = Object.factory(wave_classname)
        recordings_classname ="_VoiceRecording"
        recordings = Object.factory(recordings_classname)

        # Get latest
        alphaBrainWaveInstance = waves.Query.get(sessionId = sessionId, type = "alpha")
        recording = recordings.Query.get(sessionId = sessionId)

        # Fetch file
        response = urllib2.urlopen(recording.data.url.replace("https", "http", 1))
        print("url", recording.data.url.replace("https", "http", 1))
        audioFile = response.read()
        print("TYPE ", type(audioFile))

        # Write downloaded file to disk
        with open(recFilename + ".ogg", 'wb') as out: 
                out.write(audioFile) 
            
        process = call("/usr/bin/ffmpeg -y -i  " + recFilename + ".ogg " +  recFilename +  ".wav", shell = True)
        # Size of the reading slice in seconds
        sliceSize = 3
        maxKeyPoints, minKeyPoints = getKeyPoints(alphaBrainWaveInstance, sliceSize)
        maxKeyWords = getKeyWords(recFilename + ".wav", maxKeyPoints, sliceSize)
        minKeyWords = getKeyWords(recFilename + ".wav", minKeyPoints, sliceSize)
        keyWordStore[sessionId] = [maxKeyWords, minKeyWords]    

	return json.dumps(keyWordStore[sessionId])
        #recognize(recFilename + ".wav")

@app.route("/getresult", methods=['POST'])
def getresult():
    if request.method == 'POST':
        session_id = request.form["sessionId"]
        return json.dumps(keyWordStore[session_id])
        

def getKeyPoints(readings, sliceSize):
    # Assume that voice recording is longer than readings time

    recording_length = (readings.createdAt -readings.startTime).total_seconds()

    readingsPerS = int(len(readings.absolute) / recording_length)  

    maxReadings = {}
    minReadings = {}

    for i in xrange(0,int(recording_length), int(sliceSize)):
        sliceMax = -1.5
        sliceMin = 1.5
        for j in xrange(i, (i * 2) - 1):
            sliceMax = max(sliceMax, readings.absolute[j])
            sliceMin = min(sliceMin, readings.absolute[i])

        maxReadings[i/sliceSize] = sliceMax  
        minReadings[i/sliceSize] = sliceMin
    return (maxReadings, minReadings)

# from http://www.swharden.com/wp/2008-11-17-linear-data-smoothing-in-python/
def smoothList(list, strippedXs=False, degree=10):
    if strippedXs == True: return Xs[0:-(len(list) - (len(list) - degree + 1))]

    smoothed = [0] * (len(list) - degree + 1)

    for i in range(len(smoothed)):
        smoothed[i] = sum(list[i:i + degree]) / float(degree)

    return smoothed

def disp(instance):

    recording_length = (instance.createdAt - instance.startTime).total_seconds()
    slice = recording_length / len(instance.absolute)
    
    reading_y = instance.absolute
    reading_x = np.arange(0, float(recording_length), float(slice))

    smooth_y = smoothList(reading_y)

    # Create a trace
    smooth = go.Scatter(
        x = reading_x,
        y = smooth_y
    )

    original = go.Scatter(
        x = reading_x,
        y = reading_y
    )

    data = [smooth, original]

    py.plot(data, filename='basic-line')

def getKeyWords(audioFilename, readings, sliceSize):
    
    keyWords = {}

    voiceRec = wave.open(audioFilename,'rb')
    frameRate = voiceRec.getframerate()
    length = voiceRec.getnframes() / frameRate

    for sliceNum in readings: 

        # Calculate cut points
        startFrame = frameRate * sliceNum * sliceSize
        endFrame = startFrame + frameRate * sliceSize
        print ("Slice ", sliceNum, " startFrame", startFrame, " endFrame", endFrame)

        # Cut inital audio
        segmentName = "segment_tmp.wav"
        audioSegment = wave.open(segmentName,"wb")

        voiceRec.readframes(startFrame)
        frames = voiceRec.readframes(int(endFrame - startFrame))

        # Write segment to disk
        audioSegment.setparams(voiceRec.getparams())
        audioSegment.writeframes(frames)
        audioSegment.close()

        # Recognize segment
        recognizedText = recognize(segmentName)
        keyWords[recognizedText] = readings[sliceNum]
        voiceRec.rewind()
    voiceRec.close()

    return keyWords

def main():
    sessionId = "RM96da4ad1b4f1e48fc1458e5e6a492073"
    wave_classname = "_Wave"
    waves = Object.factory(wave_classname)
    recordings_classname ="_VoiceRecording"
    recordings = Object.factory(recordings_classname)

    # Get latest
    alphaBrainWaveInstance = waves.Query.get(sessionId = sessionId, type = "alpha")
    recording = recordings.Query.get(sessionId = sessionId)

    # Fetch file
    response = urllib2.urlopen(recording.data.url.replace("https", "http", 1))
    print("url", recording.data.url.replace("https", "http", 1))
    audioFile = response.read()
    print("TYPE ", type(audioFile))

    # Write downloaded file to disk
    with open(recFilename + ".ogg", 'wb') as out: 
            out.write(audioFile) 
        
    process = call("/usr/bin/ffmpeg -y -i  " + recFilename + ".ogg " +  recFilename +  ".wav", shell = True)
    # Size of the reading slice in seconds
    sliceSize = 5
    maxKeyPoints, minKeyPoints = getKeyPoints(alphaBrainWaveInstance, sliceSize)
    maxKeyWords = getKeyWords(recFilename + ".wav", maxKeyPoints, sliceSize)
    minKeyWords = getKeyWords(recFilename + ".wav", minKeyPoints, sliceSize)
    keyWordStore[sessionId] = [maxKeyWords, minKeyWords]    
    
if __name__ == "__main__":
    #main()
    print("done")
