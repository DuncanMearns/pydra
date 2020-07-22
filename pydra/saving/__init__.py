from ..core import SavingWorker
import cv2


class NoSaver(SavingWorker):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def dump(self, *args):
        return


class VideoSaver(SavingWorker):

    def __init__(self, video_path, fourcc: str, frame_rate: float, frame_size: tuple, **kwargs):
        super().__init__(**kwargs)
        self.video_path = video_path
        self.fourcc = fourcc
        self.frame_rate = frame_rate
        self.frame_size = frame_size

    def setup(self):
        fourcc = cv2.VideoWriter_fourcc(*self.fourcc)
        self.writer = cv2.VideoWriter(self.video_path, fourcc, self.frame_rate, self.frame_size, False)
        return

    def dump(self, frame_number, timestamp, frame, tracking):
        print(frame_number)
        self.writer.write(frame)
        return

    def cleanup(self):
        self.writer.release()
        return
