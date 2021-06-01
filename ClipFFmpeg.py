import subprocess
from pathlib import Path
import os


def concatSubClips(subCLips, outputPath):
    with open('_tempSubclipList.txt', 'w') as f:
        for clip in subCLips:
            f.write(f'file \'{str(clip.filePath)}\'\n')
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i',
                   '_tempSubclipList.txt', str(outputPath)])
    os.remove('_tempSubclipList.txt')


class SubClipFFmpeg:
    def __init__(self, videoPath, startMs, endMs) -> None:
        # start and end indicate when the subclip begins and when it ends
        vp = Path(videoPath).resolve(True)
        num = 0
        while True:
            self.filePath = vp.parent / \
                f'_temp-{vp.stem}'/f'{vp.stem}_subclip_{num}{vp.suffix}'
            if self.filePath.exists():
                num += 1
                continue
            else:
                break
        self.filePath.parent.mkdir(parents=True, exist_ok=True)
        # print('Subclip:', f'{startMs//1000}.{startMs%1000:03}', f'{(endMs-startMs)//1000}.{(endMs-startMs)%1000:03}')
        subprocess.run(['ffmpeg', '-i', str(videoPath), '-ss', f'{startMs//1000}.{startMs%1000:03}', '-to',
                       f'{(endMs)//1000}.{(endMs)%1000:03}', str(self.filePath)], capture_output=True)

    # def __del__(self):
    #     self.filePath.unlink()
    #     parentDir = self.filePath.parent
    #     if len(list(parentDir.iterdir())) == 0:
    #         parentDir.rmdir()
