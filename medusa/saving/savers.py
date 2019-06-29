import numpy as np


class Saver(object):

    def __init__(self, *args, **kwargs):
        super(Saver, self).__init__()

    def append(self, frame_number, timestamp, laser_status):
        pass

    def dump(self):
        pass


class VideoSaver(Saver):

    def __init__(self, path):
        Saver.__init__(self)
        self.metadata = []
        self.path = path

    def append(self, frame_number, timestamp, laser_status):
        self.metadata.append((frame_number, timestamp, laser_status))

    def dump(self):
        metadata = np.array(self.metadata)
        np.save(self.path + '.npy', metadata)


class TailSaver(Saver):

    def __init__(self, *args, **kwargs):
        super(TailSaver, self).__init__()
        self.metadata = []
        self.tail_point_cache = args[0]
        self.tail_points = []
        self.path = kwargs.get('path')

    def append(self, frame_number, timestamp, laser_status):
        self.metadata.append((frame_number, timestamp, laser_status))
        points = self.tail_point_cache.popleft()
        self.tail_points.append(points)

    def dump(self):
        metadata = np.array(self.metadata)
        np.save(self.path + '.npy', metadata)
        tail_points = np.array(self.tail_points)
        np.save(self.path + '_tail.npy', tail_points)
