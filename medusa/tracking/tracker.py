import numpy as np
import cv2
import math


class Tracker(object):
    """Class passed to a tracker thread when no tracking is performed"""

    def __init__(self, **kwargs):
        super(Tracker, self).__init__()

    def track_frame(self, frame_number, timestamp, laser_status, frame):
        return []


class TailTracker(Tracker):
    """Class for handling tail tracking"""

    def __init__(self, head, tail_length, num_points=9):
        super(TailTracker, self).__init__()
        self.head = head
        self.tail_length = tail_length
        self.num_points = num_points

    def track_frame(self, frame_number, timestamp, laser_status, frame):
        frame = np.asarray(frame/np.max(frame))
        tail_points = [self.head]
        width = self.tail_length
        x = self.head[0]
        y = self.head[1]
        img_filt = np.zeros(frame.shape)
        img_filt = cv2.boxFilter(frame, -1, (7,7), img_filt)
        lin = np.linspace(0,np.pi,20)
        for j in range(self.num_points):
            try:
                # Find the x and y values of the arc
                xs = x+width/self.num_points*np.sin(lin)
                ys = y+width/self.num_points*np.cos(lin)
                # Convert them to integer, because of definite pixels
                xs, ys = xs.astype(int), ys.astype(int)
                # ident = np.where(img_filt[ys,xs]==max(img_filt[ys,xs]))[0][0]
                ident = np.where(img_filt[ys,xs]==min(img_filt[ys,xs]))[0][0]
                x = xs[ident]
                y = ys[ident]
                lin = np.linspace(lin[ident]-np.pi/2,lin[ident]+np.pi/2,20)
                # Add point to list
                tail_points.append([x,y])
            except IndexError:
                tail_points.append(tail_points[-1])
        tailangle = float(math.atan2(np.nanmean(np.asarray(tail_points)[-3:-1,1]) -
                                     np.asarray(tail_points)[0,1],
                                     np.nanmean(np.asarray(tail_points)[-3:-1,0]) -
                                     np.asarray(tail_points)[0,0])*180.0/3.1415)
        return np.asarray(tail_points), tailangle*-1
