import io
import sys
import time
import threading

from tkinter import *
# from tkinter.ttk import *
import tkinter.messagebox as tkMessageBox
from tkinter.ttk import Combobox

from PIL import Image, ImageTk
from PyQt5.QtCore import QThread

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


class Player(Client):
    def __init__(self, master, server_addr, server_rtsp_port, server_plp_port, rtp_port, plp_port, movie_name):
        Client.__init__(self, server_addr, server_rtsp_port, server_plp_port, rtp_port, plp_port, movie_name)
        # PlayerWindow.__init__(self)
        self.playlist = []  # all the videos which can be played
        self.last_play = None  # the video player last time
        self.play_end = False  # if a video is completely played, set this to True
        self.play_speed = 1

        # self.Slider.sliderPressed.connect(lambda: self.sliderPressEvent())
        # self.Slider.sliderReleased.connect(lambda: self.sliderReleaseEvent())
        # self.PlayBtn.clicked.connect(lambda: self.play())
        # self.PauseBtn.clicked.connect(lambda: self.pause())
        # self.closeEvent = self.closeEvent

        # self.show()
        # self.getCategoryList()
        # self.refreshPlayList()
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()


    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.full_screen = False
        self.origin_height = 600
        self.origin_width = 800
        self.full_height = self.master.winfo_screenheight()

        # getting screen's width in pixels
        self.full_width = self.master.winfo_screenwidth()

        self.master.title("这是一个播放器")
        self.master.geometry('1200x700')

        play_icon = ImageTk.PhotoImage(file='icons/play.png')
        f1 = Frame(self.master, height=30, width=90)
        f1.pack_propagate(0)  # don't shrink
        # f.pack()
        f1.place(x=0, y=650)
        self.setup = Button(f1, width=30, height=30)
        # self.setup.config(image=play_icon)
        # # self.setup.image = play_icon
        #self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        #self.setup.grid(row=2, column=0, padx=2, pady=2)
        #self.setup.place(x=0, y=300, width=30, height=30)
        self.setup.pack(fill=BOTH, expand=1)

        # Create Play button
        self.start = Button(f1)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.pack(fill=BOTH)
        #self.start.grid(row=2, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=2, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=2, column=3, padx=2, pady=2)

        self.f = Frame(self.master, height=600, width=800)
        self.f.pack_propagate(0)  # don't shrink
        #f.pack()
        self.f.place(x=0, y=0)
        #f.grid(row=0, rowspan=2, column=0, columnspan=4, padx=5, pady=5)

        # self.bg = Label(f, width=800, height=600, bg='black')
        # #self.bg.grid(row=0, rowspan=2, column=0, columnspan=4, padx=5, pady=5)
        # self.bg.pack(fill=BOTH, expand=1)
        # Create a label to display the movie
        self.label = Label(self.f, width=800, height=600, bg='black')
        #self.label.grid(row=0, rowspan=2, column=0, columnspan=4, padx=5, pady=5)
        self.label.pack(fill=BOTH, expand=1)

        f2 = Frame(self.master, height=40, width=800)
        f2.pack_propagate(0)  # don't shrink
        # f.pack()
        f2.place(x=0, y=600)
        self.slider = Scale(f2, orient=HORIZONTAL, length = 800)
        #self.slider.grid(row=3, column=0, columnspan=4)
        self.slider.pack(fill=BOTH, expand=1)
        self.slider.bind("<ButtonPress>", self.sliderPressEvent)
        self.slider.bind("<ButtonRelease>", self.sliderReleaseEvent)

        self.speed_combobox = Combobox(self.master)
        self.speed_combobox['values'] = ('1倍速', '2倍速', '0.5倍速')
        self.speed_combobox.current(0)
        self.speed_combobox.grid(row=4, column=2, columnspan=1)
        self.speed_combobox.bind("<<ComboboxSelected>>", self.calculate_true_time_delay)

        self.subtitle_combobox = Combobox(self.master)
        self.subtitle_combobox['values'] = ('无', '默认')
        self.subtitle_combobox.current(1)
        self.subtitle_combobox.grid(row=4, column=3, columnspan=1)

        # self.search_frame = Frame(self.master)
        # self.search_frame.grid(row=0, column=4)
        self.search_text = Label(self.master, text='搜索：')
        #self.search_text.pack(side='left')
        self.search_text.grid(column=4, row=0, rowspan=1)

        self.search_entry = Entry(self.master)
        #self.search_entry.pack(side='left')
        self.search_entry.grid(column=5, row=0, rowspan=1)

        self.search_button = Button(self.master)
        # self.search_button.pack(side='left')
        self.search_button["text"] = "搜索"
        self.search_button["command"] = self.retrievePlayList
        self.search_button.grid(row=0, column=6, padx=2, pady=2)

        self.playlist = Listbox(self.master)
        self.playlist.grid(row=1, column=4, columnspan=3)

        self.historylist = Listbox(self.master)
        self.historylist.grid(row=2, column=4, columnspan=3)

        self.master.bind_all('<KeyPress>', self.key_press)


    def key_press(self, event):
        if event.keysym == 'p':
            if self.state == self.READY:
                self.playMovie()
            elif self.state == self.PLAYING:
                self.pauseMovie()
        elif event.keysym == 'Escape':
            if not self.full_screen:
                self.setFullScreen()
            else:
                self.exitFullScreen()

    def setFullScreen(self):
        self.full_screen = True
        self.master.attributes("-fullscreen", True)
        self.f.configure(width=self.full_width, height=self.full_height)
        # self.master.geometry("{0}x{1}+0+0".format(
        #     self.master.winfo_screenwidth(), self.master.winfo_screenheight()))

    def exitFullScreen(self):
        self.full_screen = False
        self.master.attributes("-fullscreen", False)
        self.f.configure(width=self.origin_width, height=self.origin_height)
        #self.master.geometry("1200x700")


    def initNewMovie(self):
        self.buffering = False
        self.video_frame_queue = FrameQueue(2000)
        self.audio_frame_queue = FrameQueue(2000)
        self.subtitle = {}
        self.has_subtitle = 0
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
        subtitle_info = subtitle.decode('utf-8').split('\n', 1)
        self.subtitle[subtitle_no] = subtitle_info[1]
        self.subtitle[subtitle_no+int(subtitle_info[0])] = ''

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

    def updateFrame(self, img):
        """Update the image file as video frame in the GUI."""
        #img = Image.frombytes("L", (640, 480), img)
        img = Image.open(io.BytesIO(img))
        w = img.size[0]
        h = img.size[1]
        nw = self.f.winfo_width()
        nh =self.f.winfo_height()
        if w * 3 > h * 4:
            new_size = (nw, nw * h // w)
        else:
            new_size = (nh * w // h, nh)
        img = img.resize(new_size)
        photo = ImageTk.PhotoImage(img)
        self.label.configure(image=photo, height=img.size[1])
        self.label.image = photo

    @qt_exception_wrapper
    def updateMovie(self):
        try:
            while True:
                if self.play_end:
                    break
                start = time.time()
                if self.state == self.PLAYING:
                    if self.buffering and not self.endBuffering():
                        continue

                    self.buffering = False
                    # self.bufferIcon.setVisible(False)
                    if not self.video_frame_queue.isEmpty() and not self.audio_frame_queue.isEmpty():

                        c = time.time()
                        sound, audio_frame_no = self.audio_frame_queue.pop()
                        # print(audio_frame_no)
                        # threading.Thread(target=playSound, args=(sound, 44100)).start()
                        threading.Thread(target=self.audio_player.playAudio, args=(sound, self.rate)).start()

                        d = time.time()

                        # print('playsound', round(d - c, 3))
                        image, frame_no = self.video_frame_queue.pop()
                        # dif = frame_no - self.last_frame_no
                        print("diff?", audio_frame_no, frame_no)
                        time_delay = self.modified_time_delay
                        self.last_frame_no = frame_no
                        self.updateFrame(image)

                        self.setSliderPosition(frame_no)
                        end = time.time()
                        interval = round(end - start, 3)
                        time_delay -= interval

                        if self.has_subtitle:
                            if frame_no in self.subtitle.keys():
                                self.SubtitleText.setText(self.subtitle[frame_no])
                        # print('slleep', time_delay)
                        a = time.time()
                        time.sleep(max(time_delay, 0))
                        b = time.time()
                        if frame_no == self.video_frame_count - 1:
                            break
                        # print('actuaaly', round(b - a, 3))
                if self.state == self.PLAYING and self.needBuffering() and not self.buffering:
                    print("found problem")
                    self.buffering = True
                    # self.bufferIcon.setVisible(True)
                    print("found again")
                    # threading.Thread(target=self.bufferShowing).start()
                elif self.teardownAcked:
                    break
        except Exception as e:
            print("update crashed", str(e))
        # self.sendRtspRequest(self.TEARDOWN)

    @qt_exception_wrapper
    def sliderPressEvent(self, event):
        self.pauseMovie()

    @qt_exception_wrapper
    def sliderReleaseEvent(self, event):
        self.video_frame_queue.jump()
        self.audio_frame_queue.jump()
        total = 100
        cur = self.slider.get()
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
        value = frame_no * 100 // (self.video_frame_count - 1)
        self.slider.set(value)

    @qt_exception_wrapper
    def calculate_true_time_delay(self, event):
        """
        calculate true time delay according to play speed
        :return: None
        """
        print("selected")
        self.play_speed = int(self.speed_combobox.current())
        if self.play_speed == 0:
            self.rate = 1
            self.modified_time_delay = self.time_delay
        elif self.play_speed == 1:
            self.rate = 2
            self.modified_time_delay = round(0.5 / self.video_fps, 3)
        elif self.play_speed == 2:
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

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else: # When the user presses cancel, resume playing.
            self.playMovie()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = Player('127.0.0.1', 10001, 10002, 'test.jpg')
    sys.exit(app.exec_())
