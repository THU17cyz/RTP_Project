import sys
import time
import threading
from audio_player import playSound
from extract_frame import FrameExtractor
from pyqt5_ui import PlayerWindow
from PyQt5.QtWidgets import QApplication
from Client import Client

import ctypes
from ctypes import wintypes

winmm = ctypes.WinDLL('winmm')
# from ctypes import windll #new

# timeBeginPeriod = windll.winmm.timeBeginPeriod #new
winmm.timeBeginPeriod(1) #new
print("set accuracy")

class FrameQueue:
    def __init__(self, capacity, thresh=100):
        self.capacity = capacity  # maximum length of queue
        self.queue = [None] * self.capacity
        self.length = 0
        self.start_ptr = 0
        self.end_ptr = 0
        self.thresh = thresh

    def isEmpty(self):
        return self.length == 0

    def isFull(self):
        return self.length == self.capacity

    def push(self, frame, frame_no):
        self.queue[self.end_ptr] = (frame, frame_no)
        self.end_ptr += 1
        self.end_ptr %= self.capacity
        self.length += 1

    def pop(self):
        frame, frame_no = self.queue[self.start_ptr]
        self.start_ptr += 1
        self.start_ptr %= self.capacity
        self.length -= 1
        return frame, frame_no

    def jump(self):
        self.start_ptr = self.end_ptr
        self.length = 0

    def reachThresh(self):
        return self.length > self.thresh

    def last(self):
        if self.start_ptr == self.end_ptr:
            return None
        last = self.end_ptr - 1
        if last == -1:
            last = self.capacity - 1
        return self.queue[last][1]




class Player(Client, PlayerWindow):
    def __init__(self, serveraddr, serverport, server_plp_port, rtpport, plp_port, movie_name):
        Client.__init__(self, serveraddr, serverport, server_plp_port, rtpport, plp_port, movie_name)
        PlayerWindow.__init__(self)
        self.playlist = []  # all the videos which can be played
        self.last_play = None  # the video player last time
        self.play_end = False  # if a video is completely played, set this to True
        self.video_frame_queue = FrameQueue(2000)
        self.audio_frame_queue = FrameQueue(2000)
        self.Slider.sliderPressed.connect(self.sliderPressEvent)
        self.Slider.sliderReleased.connect(self.sliderReleaseEvent)
        self.PlayBtn.clicked.connect(self.play)
        self.PauseBtn.clicked.connect(self.pause)
        self.closeEvent = self.closeEvent
        self.buffering = False
        self.last_frame_no = 0
        self.lock = False
        self.show()
        self.refreshPlayList()
        threading.Thread(target=self.updateMovie).start()
        # self.time_delay = round(1 / self.video_fps, 3)
        # self.modified_time_delay = 0

    def collectFrame(self, image, frame_no):
        self.video_frame_queue.push(image, frame_no)

    def collectAudioFrame(self, sound, frame_no):
        self.audio_frame_queue.push(sound, frame_no)

    def needBuffering(self):
        return self.video_frame_queue.isEmpty() and self.frameNbr != self.video_frame_count - 1
               # and self.video_frame_queue.last() != self.video_frame_count - 1 \

    def endBuffering(self):
        return self.video_frame_queue.reachThresh() or \
               self.video_frame_queue.last() == self.video_frame_count - 1 \

    def updateMovie(self):

        while True:
            start = time.time()
            if self.state == self.PLAYING:
                if self.buffering and not self.endBuffering():

                    continue

                self.buffering = False
                self.bufferIcon.setVisible(False)
                if not self.video_frame_queue.isEmpty():
                    sound, audio_frame_no = self.audio_frame_queue.pop()
                    threading.Thread(target=playSound, args=(sound,)).start()

                    image, frame_no = self.video_frame_queue.pop()
                    # with open("cache.jpg", "wb") as f:
                    #     f.write(image)
                    # print(frame_no)
                    # dif = frame_no - self.last_frame_no
                    time_delay = self.modified_time_delay
                    self.last_frame_no = frame_no
                    self.getFrame(image)
                    self.setSliderPosition(frame_no)
                    end = time.time()
                    interval = round(end - start, 3)
                    time_delay -= interval
                    print('slleep', time_delay)
                    a = time.time()
                    time.sleep(max(time_delay, 0))
                    b = time.time()
                    print('actuaaly', round(b - a, 3))
            if self.state == self.PLAYING and self.needBuffering() and not self.buffering:
                print("found problem")
                self.buffering = True
                self.bufferIcon.setVisible(True)
                threading.Thread(target=self.bufferShowing).start()
                pass
            elif self.teardownAcked:
                break

    def sliderPressEvent(self):
        self.pauseMovie()

    def sliderReleaseEvent(self):
        self.video_frame_queue.jump()

        total = self.Slider.maximum()
        cur = self.Slider.value()
        time_total = self.video_frame_count
        time_cur = time_total * cur // total
        print(time_cur)
        self.playMovie(time_cur)


    def play(self):
        self.playMovie()


    def pause(self):
        self.pauseMovie()

    def setSliderPosition(self, frame_no):
        # value = self.frameNbr * self.Slider.maximum() // self.video_frame_count
        value = frame_no * self.Slider.maximum() // (self.video_frame_count - 1)
        self.Slider.setValue(value)

    def calculate_true_time_delay(self):
        if self.play_speed == self.ORIGIN_SPEED:
            self.modified_time_delay = self.time_delay
        elif self.play_speed == self.DOUBLE_SPEED:
            self.modified_time_delay = round(0.5 / self.video_fps, 3)
        elif self.play_speed == self.HALF_SPEED:
            self.modified_time_delay = round(2 / self.video_fps, 3)

    def closeEvent(self, event):
        self.exitAttempt()

    def refreshPlayList(self):
        play_list = self.retrievePlayList()
        for movie in play_list:
            self.PlayList.addItem(movie)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = Player('127.0.0.1', 10001, 10002, 'test.jpg')
    sys.exit(app.exec_())