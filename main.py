import argparse
from moviepy.editor import VideoFileClip, preview, concatenate_videoclips
from pathlib import Path
from progress.bar import Bar

SAMPLE_RATE = 12000


def findFirstSilence(video_samples, minInRow, threshold, step=1):
    # step other than 1 is untested but might dramatically improve performance
    silenceStart = -1
    silenceEnd = -1
    samplesInRow = 0
    # algorithm that finds first long enough silence in video
    for i in range(0, len(video_samples), step):
        if threshold>max(video_samples[i])>-threshold:
            if samplesInRow==0:
                silenceStart=i
                samplesInRow = 1
            else:
                samplesInRow+=1*step
        else:
            if samplesInRow>0:
                if samplesInRow>=minInRow:
                    silenceEnd = i
                    break
                else:
                    samplesInRow = 0
            else:
                continue
    if silenceStart!=-1 and silenceEnd!=-1:
        found = True
    else:
        found=False
    return (silenceStart, silenceEnd), found


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
    parser.add_argument('-p', '--preview', action='store_true', help='previews with the silence cutout')
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

    startSearchAt=0
    # ACTUAL SCRIPT
    video = VideoFileClip(str(inputPath))
    videoDuration = video.duration *1000
    clipsWithSound = []
    analyzedClipDuration = 0
    if not args.verbose:
        bar = Bar('finding parts of video with sound', max=video.duration*1000, suffix = '%(percent).1f%% - %(eta)ds')
        bar.next(n=0)
    while True:
        if args.verbose:
            print(f'Video time to analyze: {getTimeStr(video.duration*1000)}')
        samples = video.audio.to_soundarray(fps=SAMPLE_RATE, nbytes=2)

        indices, found = findFirstSilence(samples, minimalSamplesInRow, args.threshold)
        if found:
            startMs = indices[0]//(SAMPLE_RATE//1000) + args.startPadding
            endMs = indices[1]//(SAMPLE_RATE//1000) - args.endPadding
            beforeSilence = video.subclip(t_end=getTimeStr(startMs))
            if args.verbose:
                print(f'Cutting out:', getTimeStr(analyzedClipDuration+startMs), '-', getTimeStr(analyzedClipDuration+endMs))
            else:
                bar.next(n=endMs)
            analyzedClipDuration += endMs
            clipsWithSound.append(beforeSilence)
            if endMs<(video.duration *1000) - 50:
                video = video.subclip(t_start=getTimeStr(endMs))
            continue
        else:
            # adds all the remaining part of video
            clipsWithSound.append(video)
            if not args.verbose:
                bar.next(n=video.duration*1000)
            break
    if not args.verbose:
        bar.finish()
    final = concatenate_videoclips(clipsWithSound)
    if args.preview:
        final.preview()
    else:
        print('Writing to file')
        final.write_videofile(str(outputPath), threads=args.threads, codec='libx264', rewrite_audio=False,temp_audiofile='audio_temp.aac', ffmpeg_params=['-crf', str(args.crf)])