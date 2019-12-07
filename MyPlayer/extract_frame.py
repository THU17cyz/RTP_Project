import cv2
import imageio
import skimage
import os
import time
from PyQt5.QtCore import pyqtSignal, QThread
import numpy as np
# imageio.plugins.ffmpeg.download()


class VideoCapturer:
    def __init__(self, video, cache_path):
        super(VideoCapturer, self).__init__()
        self.video = cv2.VideoCapture(video)
        self.playing = True
        self.fps = None
        self.frame_weight = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))  # 3 is cv2.CAP_PROP_FRAME_WIDTH
        self.frame_height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))  # 4 is cv2.CAP_PROP_FRAME_HEIGHT
        self.frame_count = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))  # 7 is cv2.CAP_PROP_FRAME_COUNT
        self.fps = int(self.video.get(cv2.CAP_PROP_FPS))  # 5 is cv2.CAP_PROP_FPS
        self.cache_path = cache_path
        self.frame_no = 0

    def captureFrame(self, pos=-1):
        #print(pos)
        if pos == -1:
            self.frame_no += 1
        else:
            self.frame_no = pos
            self.video.set(cv2.CAP_PROP_POS_FRAMES, self.frame_no)
        success, image = self.video.read()
        if success:
            data = cv2.imencode('.jpg', image)[1].tobytes()
            return data, self.frame_no


class FrameExtractor(QThread):
    next_frame_signal = pyqtSignal(str)

    def __init__(self, video):
        super(FrameExtractor, self).__init__()
        self.video = cv2.VideoCapture(video)
        # self.video = imageio.get_reader(video, 'ffmpeg')
        self.playing = True
        self.fps = None
        self.frame_weight = None
        self.frame_height = None

    def run(self):
        # for num, im in enumerate(self.video):
        #     # image的类型是mageio.core.util.Image可用下面这一注释行转换为arrary
        success = True
        num = 0
        while success and self.playing:
            #self.video.set(cv2.CAP_PROP_POS_MSEC, num * 1000) # 1s
            success, image = self.video.read()
            img_name = str(num) + '.jpg'
            cv2.imwrite(img_name, image)

            #return img_name
            self.next_frame_signal.emit(img_name)
            num += 1
            time.sleep(0.01)
            if num > 0:
                self.remove(num-1)

    def remove(self, num):
        img_name = str(num) + '.jpg'
        os.remove(img_name)

