from pydra import Pydra, Acquisition, VideoSaver, FRAME
import time
import numpy as np


class VideoDummy(Acquisition):

    name = "video"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.i = 0

    @FRAME
    def acquire(self):
        self.i += 1
        # Do some actual work
        js = np.random.rand(1000)
        k = [np.log(j + np.sqrt(j)) for j in js]
        t = time.time()
        i = self.i
        return t, i, np.zeros((200, 300), dtype="uint8")


VIDEO = {
    "worker": VideoDummy,
    "params": {}
}


class MySaver(VideoSaver):

    name = "mysaver"
    workers = ("video",)

    def recv_frame(self, t, i, frame, **kwargs):
        super().recv_frame(t, i, frame, **kwargs)


modules = [VIDEO]
savers = [MySaver]


def main():
    pydra = Pydra.run(modules=modules, savers=savers)
    time.sleep(3.)
    pydra.exit()


if __name__ == "__main__":
    main()
