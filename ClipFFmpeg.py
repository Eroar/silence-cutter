import subprocess
from pathlib import Path
import os

def concatSubClips(subCLips, outputPath):
    with open('_tempSubclipList.txt', 'w') as f:
        for clip in subCLips:
            f.write(f'file \'{clip.filePath}\'\n')
    subprocess.run(['ffmpeg', '-f', 'concat', '-i',
                   '_tempSubclipList.txt', '-c', 'copy', str(outputPath)])
    os.remove('_tempSubclipList.txt')


class SubClipFFmpeg:
    def __init__(self, videoPath, startMs, endMs) -> None:
        # start and end indicate when the subclip begins and when it ends
        vp = Path(videoPath)
        num = 0
        while True:
            self.filePath = vp.with_name(f'{vp.stem}_subclip_{num}{vp.suffix}')
            if self.filePath.exists():
                num += 1
                continue
            else:
                break
        subprocess.run(['ffmpeg', '-ss', f'{startMs//1000}.{startMs%1000:03}', '-i', str(
            videoPath), '-c', 'copy', '-t', f'{(endMs-startMs)//1000}.{(endMs-startMs)%1000:03}', str(self.filePath)])

    def __del__(self):
        self.filePath.unlink()
