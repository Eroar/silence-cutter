import argparse
from moviepy.audio.AudioClip import AudioArrayClip
from moviepy.editor import VideoFileClip, preview
from moviepy.audio.io.AudioFileClip import AudioFileClip
from pathlib import Path
import numpy as np
from datetime import timedelta

# PARSING ARGS
parser = argparse.ArgumentParser(
    description='Cuts silence out of video file based on arguments.')
parser.add_argument('input')
parser.add_argument('-o', '--output')
parser.add_argument('-min', '--minimalSilence', type=int, default=250, help='minimal silence length in ms')
parser.add_argument('-start', '--startPadding', type=int, default=100, help='amount of time that is not cut from the beginning of silence')
parser.add_argument('-end', '--endPadding', type=int, default=100, help='amount of time that is not cut from the end of silence')
parser.add_argument('-t', '--threshold', type=float, default=0.001, help='maximal noise value to be considered as sound')
parser.add_argument('-p', '--preview', action='store_true', help='previews with the silence cutout')
args = parser.parse_args()

minimalSamplesInRow = int(44*args.minimalSilence)
print('minimal samples in row:', minimalSamplesInRow)


inputPath = Path(args.input)
if args.output:
    outputPath = Path(args.output)
else:
    outputPath = inputPath.with_name("output.mp4")
minSilence = args.minimalSilence
startPadding = args.startPadding
endPadding = args.endPadding
threshold = args.threshold

if minSilence<startPadding+endPadding:
    print('minimalSilence smaller than startPadding + endPadding')
    quit()

video = VideoFileClip(str(inputPath))
samples = video.audio.to_soundarray(fps=44000, nbytes=2)

print('Finding silent indices')
silentIndices = []
for i,s in enumerate(samples):
    if threshold>max(s)>-threshold:
        silentIndices.append(i)

silentIndicesSlices = []
print('Checking samples in row')
samplesInRow=1
for i, index in enumerate(silentIndices):
    # this algorithms has to begin with the second item
    if i==0:
        continue
    
    # if the index is in row, continue
    if index-1==silentIndices[i-1] and i+1!=len(silentIndices):
        samplesInRow+=1
        continue
    # if the index is not in row
    else:
        if samplesInRow>=minimalSamplesInRow:
            silenceStart = i-samplesInRow
            silenceEnd = i-1
            silentIndicesSlices.append((silenceStart, silenceEnd))
        samplesInRow=1

def getTimeStr(timeInMs):
    ms = int(timeInMs %1000)
    s = int((timeInMs//1000) %60)
    m = int((timeInMs//(1000*60))% 60)
    h = int((timeInMs//(1000*60*60))% 24)
    return f"{h}:{m}:{s}.{ms}"

print('Slices that have been found:')
for slice in silentIndicesSlices:
    print(f'{getTimeStr(slice[0]/44)} - {getTimeStr(slice[1]/44)}')

print('Cutting video')
for slice in silentIndicesSlices:
    startMs = slice[0]/44 + startPadding
    endMs = slice[1]/44 - endPadding
    cutStart = getTimeStr(startMs)
    cutEnd = getTimeStr(endMs)
    video = video.cutout(cutStart, cutEnd)
if args.preview:
    video.preview()
else:
    video.write_videofile(str(outputPath))
video.close()