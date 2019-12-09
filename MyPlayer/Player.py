import sys
import time
import threading
from audio_player import AudioPlayer
from subtitle import Subtitle
from pyqt5_ui import PlayerWindow
from PyQt5.QtWidgets import QApplication
from Client import Client
import ctypes
from PyQt5.QtWidgets import QMessageBox

winmm = ctypes.WinDLL('winmm')
winmm.timeBeginPeriod(1)


def qt_exception_wrapper(func):
    def wrapper(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except Exception as e:
            QMessageBox.information(self, 'Error', 'Meet with Error: ' + str(e),
                QMessageBox.Yes, QMessageBox.Yes)
    return wrapper

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
    def __init__(self, server_addr, server_rtsp_port, server_plp_port, rtp_port, plp_port, movie_name):
        Client.__init__(self, server_addr, server_rtsp_port, server_plp_port, rtp_port, plp_port, movie_name)
        PlayerWindow.__init__(self)
        self.playlist = []  # all the videos which can be played
        self.last_play = None  # the video player last time
        self.play_end = False  # if a video is completely played, set this to True

        self.Slider.sliderPressed.connect(lambda: self.sliderPressEvent())
        self.Slider.sliderReleased.connect(lambda: self.sliderReleaseEvent())
        self.PlayBtn.clicked.connect(lambda: self.play())
        self.PauseBtn.clicked.connect(lambda: self.pause())
        self.closeEvent = self.closeEvent

        self.show()
        self.getCategoryList()
        self.refreshPlayList()

        # self.time_delay = round(1 / self.video_fps, 3)
        # self.modified_time_delay = 0
    def initNewMovie(self):
        self.buffering = False
        self.video_frame_queue = FrameQueue(2000)
        self.audio_frame_queue = FrameQueue(2000)
        self.subtitle = {}
        self.last_frame_no = 0
        self.lock = False
        self.rate = 1
        threading.Thread(target=self.updateMovie).start()

    def collectFrame(self, image, frame_no):
        self.video_frame_queue.push(image, frame_no)

    def collectAudioFrame(self, sound, frame_no):
        self.audio_frame_queue.push(sound, frame_no)

    def collectSubtitle(self, subtitle, subtitle_no):
        # self.subtitle.generateFrame2Subtitle(subtitle, subtitle_no)
        print("heyyyyyyyyyyyyyyyyyy")
        self.subtitle[subtitle_no] = subtitle.decode('utf-8')

    def needBuffering(self):
        video_need = self.video_frame_queue.isEmpty() and self.frameNbr != self.video_frame_count - 1
        audio_need = self.audio_frame_queue.isEmpty() and self.frameNbr != self.video_frame_count - 1

        return video_need or audio_need
               # and self.video_frame_queue.last() != self.video_frame_count - 1 \

    def endBuffering(self):
        video_end = self.video_frame_queue.reachThresh() or \
                    self.video_frame_queue.last() == self.video_frame_count - 1
        audio_end = self.audio_frame_queue.reachThresh() or \
                    self.audio_frame_queue.last() == self.video_frame_count - 1
        return video_end and audio_end

    @qt_exception_wrapper
    def updateMovie(self):
        while True:
            if self.play_end:
                break
            start = time.time()
            if self.state == self.PLAYING:
                if self.buffering and not self.endBuffering():
                    continue

                self.buffering = False
                self.bufferIcon.setVisible(False)
                if not self.video_frame_queue.isEmpty() and not self.audio_frame_queue.isEmpty():

                    c = time.time()
                    sound, audio_frame_no = self.audio_frame_queue.pop()
                    print(audio_frame_no)
                    #threading.Thread(target=playSound, args=(sound, 44100)).start()
                    threading.Thread(target=self.audio_player.playAudio, args=(sound, self.rate)).start()

                    d = time.time()

                    #print('playsound', round(d - c, 3))
                    image, frame_no = self.video_frame_queue.pop()
                    # dif = frame_no - self.last_frame_no
                    time_delay = self.modified_time_delay
                    self.last_frame_no = frame_no
                    self.getFrame(image)
                    # self.setSliderPosition(frame_no)
                    end = time.time()
                    interval = round(end - start, 3)
                    time_delay -= interval

                    if frame_no in self.subtitle.keys():
                        print(self.subtitle[frame_no])
                        self.SubtitleText.setText(self.subtitle[frame_no])
                    #print('slleep', time_delay)
                    a = time.time()
                    time.sleep(max(time_delay, 0))
                    b = time.time()
                    if frame_no == self.video_frame_count - 1:
                        break
                    #print('actuaaly', round(b - a, 3))
            if self.state == self.PLAYING and self.needBuffering() and not self.buffering:
                print("found problem")
                self.buffering = True
                self.bufferIcon.setVisible(True)
                print("found again")
                threading.Thread(target=self.bufferShowing).start()
            elif self.teardownAcked:
                break
        # self.sendRtspRequest(self.TEARDOWN)

    @qt_exception_wrapper
    def sliderPressEvent(self):
        self.pauseMovie()

    @qt_exception_wrapper
    def sliderReleaseEvent(self):
        self.video_frame_queue.jump()
        self.audio_frame_queue.jump()
        total = self.Slider.maximum()
        cur = self.Slider.value()
        time_total = self.video_frame_count
        time_cur = time_total * cur // total
        print(time_cur)
        self.playMovie(time_cur)

    @qt_exception_wrapper
    def play(self):
        self.playMovie()

    @qt_exception_wrapper
    def pause(self):
        self.pauseMovie()

    @qt_exception_wrapper
    def setSliderPosition(self, frame_no):
        # value = self.frameNbr * self.Slider.maximum() // self.video_frame_count
        value = frame_no * self.Slider.maximum() // (self.video_frame_count - 1)
        self.Slider.setValue(value)

    @qt_exception_wrapper
    def calculate_true_time_delay(self):
        """
        calculate true time delay according to play speed
        :return: None
        """
        if self.play_speed == self.ORIGIN_SPEED:
            self.rate = 1
            self.modified_time_delay = self.time_delay
        elif self.play_speed == self.DOUBLE_SPEED:
            self.rate = 2
            self.modified_time_delay = round(0.5 / self.video_fps, 3)
        elif self.play_speed == self.HALF_SPEED:
            self.rate = 0.5
            self.modified_time_delay = round(2 / self.video_fps, 3)

    def closeEvent(self, event):
        self.exitAttempt(event)

    def refreshPlayList(self, keyword=''):
        self.PlayList.clear()
        play_list = self.retrievePlayList('SEARCH', keyword, self.CategoryComboBox.currentData())
        print(self.CategoryComboBox.currentData()=='')
        for movie in play_list:
            self.PlayList.addItem(movie)

    def getCategoryList(self):
        self.CategoryComboBox.clear()
        self.CategoryComboBox.addItem('all', '')
        category_list = self.retrievePlayList('CATEGORY')
        for category in category_list:
            self.CategoryComboBox.addItem(category, category)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = Player('127.0.0.1', 10001, 10002, 'test.jpg')
    sys.exit(app.exec_())
