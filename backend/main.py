import os, plotly
os.environ["PARSE_API_ROOT"] = "http://95.85.22.29/parse"

# Everything else same as usual
from configuration import configure
from parse_rest.datatypes import Object
from parse_rest.connection import register
from parse_rest.user import User

import numpy as np
import plotly.plotly as py
import plotly.graph_objs as go
import wave

configure()
    
def getKeyWords(voiceRec, readings):
    keyWords = []

    return keyWords
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

def main():
    
    wave_classname = "_Wave"
    waves = Object.factory(wave_classname)

    recordings_classname ="_VoiceRecording"
    recordings = Object.factory(recordings_classname)

    # Get latest
    instance = waves.Query.all()[len(waves.Query.all()) - 1]
    #recording = recordings.Query.get(sessId = instance.sessId)
    disp(instance)

    #points = getKeyPoints(recording, instance)
if __name__ == "__main__":
    main()