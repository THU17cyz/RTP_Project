import sys
import time
import threading
from extract_frame import FrameExtractor
from pyqt5_ui import PlayerWindow
from PyQt5.QtWidgets import QApplication
from Client import Client


class FrameQueue:
    def __init__(self, capacity):
        self.capacity = capacity  # maximum length of queue
        self.queue = [None] * self.capacity
        self.length = 0
        self.start_ptr = 0
        self.end_ptr = 0

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



class Player(Client, PlayerWindow):
    def __init__(self, serveraddr, serverport, rtpport, filename):
        Client.__init__(self, serveraddr, serverport, rtpport, filename)
        PlayerWindow.__init__(self)
        self.playlist = []  # all the videos which can be played
        self.last_play = None  # the video player last time
        self.play_end = False  # if a video is completely played, set this to True
        self.video_frame_queue = FrameQueue(2000)
        self.Slider.sliderPressed.connect(self.sliderPressEvent)
        self.Slider.sliderReleased.connect(self.sliderReleaseEvent)
        self.PlayBtn.clicked.connect(self.play)
        self.PauseBtn.clicked.connect(self.pause)
        self.closeEvent = self.closeEvent
        self.show()
        threading.Thread(target=self.updateMovie).start()
        #self.client = Client('127.0.0.1', 10001, 10002, 'test.jpg')

    def collectFrame(self, image, frame_no):
        self.video_frame_queue.push(image, frame_no)

    def updateMovie(self):

        while True:
            if self.state == self.PLAYING and not self.video_frame_queue.isEmpty():
                image, frame_no = self.video_frame_queue.pop()
                # with open("cache.jpg", "wb") as f:
                #     f.write(image)
                self.getFrame(image)
                self.setSliderPosition(frame_no)
                time.sleep(0.03)

    def sliderPressEvent(self):

        self.pauseMovie()

    def sliderReleaseEvent(self):
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
        value = frame_no * self.Slider.maximum() // self.video_frame_count
        self.Slider.setValue(value)

    def closeEvent(self, event):
        self.exitAttempt()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = Player('127.0.0.1', 10001, 10002, 'test.jpg')
    sys.exit(app.exec_())