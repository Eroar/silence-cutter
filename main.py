import argparse
from moviepy.editor import VideoFileClip, concatenate_videoclips
from pathlib import Path

SAMPLE_RATE = 12000

def findFirstSilence(samples, minInRow, startSearchAt=0, step=1):
    # silence in samples is True value
    # sound in samples is a False value
    # step other than 1 is untested but might dramatically improve performance
    while True:
        try:
            silenceIndex = samples.index(True,startSearchAt)
        except ValueError:
            return (-1,-1), False
        try:
            noiseIndex = samples.index(False,silenceIndex)
        except ValueError:
            return (silenceIndex, len(samples)-1), True

        if noiseIndex - silenceIndex >= minInRow:
            return(silenceIndex, noiseIndex-1), True
        else:
            startSearchAt = noiseIndex + 1
            continue

def getTimeStr(timeInMs):
    ms = int(timeInMs %1000)
    s = int((timeInMs//1000) %60)
    m = int((timeInMs//(1000*60))% 60)
    h = int((timeInMs//(1000*60*60))% 24)
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"


if __name__=="__main__":
    # PARSING ARGS
    parser = argparse.ArgumentParser(
        description='Cuts silence out of video file based on arguments.')
    parser.add_argument('input')
    parser.add_argument('-o', '--output')
    parser.add_argument('-min', '--minimalSilence', type=int, default=500, help='minimal silence length in ms')
    parser.add_argument('-start', '--startPadding', type=int, default=100, help='amount of time that is not cut from the beginning of silence')
    parser.add_argument('-end', '--endPadding', type=int, default=100, help='amount of time that is not cut from the end of silence')
    parser.add_argument('-t', '--threshold', type=float, default=0.0001, help='maximal noise value to be considered as sound')
    parser.add_argument('-v', '--verbose', action='store_true', help='prints which sections are cut off instead of progress bar')
    parser.add_argument('--threads', type=int, default=1, help='how many threads to use for final video encoding')
    parser.add_argument('-crf', type=int, default=17, help='crf of ffmpeg h264 encoding')
    args = parser.parse_args()

    if args.minimalSilence<args.startPadding+args.endPadding:
        print('minimalSilence smaller than startPadding + endPadding')
        quit()


    minimalSamplesInRow = int(SAMPLE_RATE//1000* args.minimalSilence)
    print('minimal samples in row:', minimalSamplesInRow)


    inputPath = Path(args.input)
    if args.output:

        outputPath = Path(args.output)
    else:
        outputPath = inputPath.with_name("output.mp4")

    for k,v in args.__dict__.items():
        print(k,':',v)

    startSearchAt=0
    # ACTUAL SCRIPT
    video = VideoFileClip(str(inputPath))
    audio_samples = video.audio.to_soundarray(fps=SAMPLE_RATE, nbytes=2)
    samplesLength = len(audio_samples)
    print('Scaling samples')
    tresholdSamples = list(map(lambda s: args.threshold>max(s)>-args.threshold, audio_samples))

    lastSilenceEndMs = 0
    lastEndIndex = 0
    clipsWithSound = []
    while True:
        if not args.verbose:
            print('Working:' ,round(lastEndIndex/samplesLength * 100, 2), '%', end='\r')
        if args.verbose:
            print(f'Video time to analyze: {getTimeStr(video.duration*1000)}')

        indices, found = findFirstSilence(tresholdSamples, minimalSamplesInRow, startSearchAt=lastEndIndex)
        if found:
            startMs = indices[0]//(SAMPLE_RATE//1000) + args.startPadding
            endMs = indices[1]//(SAMPLE_RATE//1000) - args.endPadding
            beforeSilence = video.subclip(t_start=getTimeStr(lastSilenceEndMs), t_end=getTimeStr(startMs))
            clipsWithSound.append(beforeSilence)
            # beforeSilence = video.subclip(t_end=getTimeStr(startMs))
            if args.verbose:
                print(f'Cutting out:', getTimeStr(lastSilenceEndMs), '-', getTimeStr(startMs))
            lastSilenceEndMs = endMs
            lastEndIndex = indices[1]
            if lastEndIndex == video.duration * SAMPLE_RATE - 1:
                print('Working:' , '100.00 %', end='\r')
                break
            else:
                continue
        else:
            # adds all the remaining part of video
            clipsWithSound.append(SubClipFFmpeg(videoPath=inputPath, startMs=lastSilenceEndMs, endMs=video.duration*1000-lastSilenceEndMs))
            break
    print('Writing to file')
    # concatSubClips(clipsWithSound, outputPath)
    final = concatenate_videoclips(clipsWithSound)
    final.write_videofile(str(outputPath), threads=args.threads, codec='libx264', temp_audiofile='outputTEMP_FILE.aac', audio_codec='aac', ffmpeg_params=['-crf', str(args.crf)])