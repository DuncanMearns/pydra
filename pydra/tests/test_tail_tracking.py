from pydra import Pydra, ports, config
from pydra.modules.cameras.workers._base import CameraAcquisition
import cv2


class VideoWorker(CameraAcquisition):

    name = "video"

    def __init__(self, filepath, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filepath = filepath

    @property
    def frame_count(self):
        return self.cap.get(cv2.CAP_PROP_FRAME_COUNT)

    def setup(self):
        self.cap = cv2.VideoCapture(self.filepath)

    def read(self):
        if self.cap.get(cv2.CAP_PROP_POS_FRAMES) >= self.frame_count:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.frame_number = 0
        ret, frame = self.cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame


VIDEO = {
    "worker": VideoWorker,
    "params": {"filepath": r"test_files\fish1_trial01.avi"}
}


config["modules"] = [VIDEO]


if __name__ == "__main__":
    config = Pydra.configure(config, ports)
    pydra = Pydra.run(working_dir="D:\pydra_tests", **config)
