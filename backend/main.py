import os, plotly
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
import plotly.plotly as py
import plotly.graph_objs as go
import soundfile      
import wave
from base64 import decodestring
from audio_transcribe import recognize

configure()
    
def getKeyPoints(voiceRec, readings):
    # Assume that voice recording is longer than readings time
    recording_length = (readings.createdAt -readings.startTime).total_seconds()
    slice = recording_length / len(readings.absolute)
    maxReadings = {}
    minReadings = {}

    for i in xrange(0,recording_length, 3*slice):
        sliceMax = -1.5
        sliceMin = 1.5
        for j in xrange(i, i * 2 - 1):
            sliceMax = max(sliceMax, readings.absolute[j])
            sliceMin = min(sliceMin, readings.absolute[i])
        maxReadings[i/ slice] = sliceMax  
        minReadings[i/slice] = sliceMin
    return maxReadings, minReadings

def getKeyWords(maxReadings, minReadings, sliceSize, voiceRec):
    keyWords = {}
    for sliceN in maxReadings: 
        wave.open(voiceRec,'rb')
        startTime = sliceN * sliceSize * 3
        endTime = startTime + sliceSize - 1
        voiceRec.readframes(startTime)
        audioSegment = voiceRec.readframes(endTime - startTime)



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
def bytes(n):
    if n== 0:
        return 1
    return int(log(n,256)+1)

def testCutting(audioFilename):
    slice = 4
    keyWords = {}
    maxReadings = {1:2, 2:3, 3:4}
    
    for sliceN in maxReadings: 
        voiceRec = wave.open(audioFilename,'rb')
        # Calculate cut points
        startTime = sliceN * slice
        endTime = startTime + slice - 1
        # Cut inital audio
        segmentName = "segment_tmp.wav"
        audioSegment = wave.open(segmentName,"wb")
        voiceRec.readframes(startTime)
        frames = voiceRec.readframes(endTime - startTime)

        # Write segment to disk
        audioSegment.setparams(voiceRec.getparams())
        audioSegment.writeframes(frames)
        audioSegment.close()

        # Recognize segment
        recognizedText = recognize(segmentName)
        keyWords[recognizedText] = maxReadings[sliceN]
        voiceRec.close()

    return keyWords

def main():
    keyWords = testCutting("man1_wb.wav")

    print(keyWords)

    wave_classname = "_Wave"
    waves = Object.factory(wave_classname)

    recordings_classname ="_VoiceRecording"
    recordings = Object.factory(recordings_classname)

    # Get latest
    instance = waves.Query.all()[0]
    recFilename = 'voice_tmp.wav'
    recording = recordings.Query.all()[0] 
    #recording = recordings.Query.get(sessId = instance.sessId)

    response = urllib2.urlopen(recording.data.url.replace("https", "http", 1))
    print("url", recording.data.url.replace("https", "http", 1))
    audioFile = response.read()
    print("TYPE ", type(audioFile))
    
    # Write downloaded file to disk
    with open(recFilename, 'wb') as out: 
            out.write(audioFile)
   # convertedFilename = "voice_tmpW.wav"
 

   # data, samplerate = soundfile.read(recFilename)
    #soundfile.write(convertedFilename, data, samplerate)
    #print(recognize(soundfile.read(recFilename)))
    #disp(instance)

    points = getKeyPoints(recording, instance)

if __name__ == "__main__":
    main()