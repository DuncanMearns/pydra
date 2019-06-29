from pyqtgraph.Qt import QtCore
from pymba import Vimba
import time
import numpy as np


class CameraThread(QtCore.QThread):
    """Class for acquiring from the cameras in a daemon thread (i.e. always running in the background)"""

    newframe = QtCore.pyqtSignal(tuple)

    def __init__(self, wh, fps, exposure=2695, gain=18):
        super(CameraThread, self).__init__()
        # Camera settings
        self.width, self.height = wh
        self.fps = fps
        self.exposure = exposure
        self.gain = gain
        # Flags
        self.connected = False
        self.acquiring = False

    def run(self):
        with Vimba() as vimba:
            print('Connecting to camera...')
            # get system object
            system = vimba.system()
            # list available cameras (after enabling discovery for GigE cameras)
            if system.GeVTLIsPresent:
                system.run_feature_command("GeVDiscoveryAllOnce")
                time.sleep(0.2)
            cameraIds = vimba.camera_ids()
            for cameraId in cameraIds:
                print('Camera ID: %s' % cameraId)
            # get and open a cameras
            camera0 = vimba.camera(cameraIds[0])
            camera0.open()
            # set the value of a feature
            camera0.AcquisitionMode = 'Continuous'
            camera0.Width = self.width #340
            camera0.Height = self.height #240
            camera0.AcquisitionFrameRate = self.fps #300
            camera0.ExposureTime = self.exposure
            camera0.Gain = self.gain

            # create frame
            frame0 = camera0.new_frame()
            # announce frame
            frame0.announce()

            camera0.start_capture()
            frame0.queue_for_capture()
            camera0.run_feature_command('AcquisitionStart')

            print('...connected to camera.\n')
            self.connected = True

            frame_counter = 0
            while self.connected:

                if self.acquiring:
                    # Run the cameras acquisition
                    frame0.wait_for_capture()
                    frame0.queue_for_capture()
                    frame = np.ndarray(buffer=frame0.buffer_data_numpy(),
                                       dtype=np.uint8,
                                       shape=(self.height, self.width, 1))[:, :, 0]
                    timestamp = time.time()
                    # Emit the frame number, timestamp and frame
                    self.newframe.emit((frame_counter, timestamp, frame))
                    frame_counter += 1

                else:
                    # Wait for acquiring to change
                    frame_counter = 0
                    time.sleep(0.02)

            # clean up after capture
            camera0.end_capture()
            camera0.run_feature_command('AcquisitionStop')
            camera0.revoke_all_frames()
            # close cameras
            camera0.close()
