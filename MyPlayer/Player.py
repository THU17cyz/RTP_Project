import io
import os
import sys
import time
import threading

from tkinter import *
# from tkinter.ttk import *
import tkinter.messagebox as tkMessageBox
from tkinter.ttk import Combobox

from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFile
from PyQt5.QtCore import QThread

from audio_player import AudioPlayer
from subtitle import Subtitle
from pyqt5_ui import PlayerWindow
from PyQt5.QtWidgets import QApplication
from Client import Client
import ctypes
from PyQt5.QtWidgets import QMessageBox

ImageFile.LOAD_TRUNCATED_IMAGES = True

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

    def top(self):
        if self.length == 0:
            return 99999999
        return self.queue[self.start_ptr][1]

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
        self.cur_frame = 0
        self.record_file = 'record/record.txt'
        self.play_record = {}


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
        if os.path.exists(self.record_file):
            with open(self.record_file, "r") as f:
                lines = f.read().split('\n')
            i = 0
            for line in lines[:-1]:
                self.historylist.insert(i, line.strip())
                i += 1
            last_movie = self.historylist.get(0)
            self.play_record[last_movie] = lines[-1].strip()
            print(last_movie)
            frame_memory = self.play_record[last_movie]
            if frame_memory != '':
                self.setupMovie(last_movie)
                frame_memory = int(frame_memory)
                self.cur_frame = frame_memory
                self.memory = frame_memory
        else:
            self.memory = ''



    def createWidgets(self):
        """Build GUI."""
        self.full_screen = False

        self.origin_height = 600
        self.origin_width = 800

        self.full_height = self.master.winfo_screenheight()
        self.full_width = self.master.winfo_screenwidth()

        self.master.title("这是一个播放器")
        self.master.geometry('1200x700')
        self.master.resizable(0, 0)
        self.master.bind_all('<KeyPress>', self.key_press)

        full_icon = Image.open('icons/fullscreen.png')
        full_icon = full_icon.resize((25, 25))
        full_icon = ImageTk.PhotoImage(full_icon)
        play_icon = Image.open('icons/play.png')
        play_icon = play_icon.resize((25, 25))
        play_icon = ImageTk.PhotoImage(play_icon)
        pause_icon = Image.open('icons/pause.png')
        pause_icon = pause_icon.resize((25, 25))
        pause_icon = ImageTk.PhotoImage(pause_icon)

        f1 = Frame(self.master, height=40, width=65)
        f1.pack_propagate(0)
        f1.place(x=210, y=650)
        self.setup = Button(f1, width=65, height=40, text = '初始化', font=15)
        self.setup['command'] = self.setupMovie
        self.setup.pack()

        f1 = Frame(self.master, height=40, width=65)
        f1.pack_propagate(0)  # don't shrink
        # f.pack()
        f1.place(x=0, y=650)
        self.setup = Button(f1, width=65, height=40, image=full_icon, text='全屏', font=15, compound=LEFT)
        self.setup.image = full_icon
        self.setup['command'] = self.setFullScreen
        self.setup.pack()

        f3 = Frame(self.master, height=40, width=65)
        f3.pack_propagate(0)
        f3.place(x=70, y=650)
        self.play = Button(f3, width=65, height=40, image=play_icon, text='播放', font=15, compound=LEFT)
        self.play.image = play_icon
        self.play['command'] = self.play1
        self.play.pack()

        self.f2 = Frame(self.master, height=40, width=65)
        self.f2.pack_propagate(0)
        self.f2.place(x=140, y=650)
        self.pause = Button(self.f2, width=65, height=40, image=pause_icon, text='暂停', font=15, compound=LEFT)
        self.pause.image = pause_icon
        self.pause['command'] = self.pauseMovie
        self.pause.pack()

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=2, column=3, padx=2, pady=2)

        f2 = Frame(self.master, height=40, width=800)
        f2.pack_propagate(0)
        f2.place(x=0, y=600)
        self.slider = Scale(f2, orient=HORIZONTAL, length=800)
        self.slider.pack(fill=BOTH, expand=1)
        self.slider['state'] = 'disabled'
        self.slider.bind("<ButtonPress>", self.sliderPressEvent)
        self.slider.bind("<ButtonRelease>", self.sliderReleaseEvent)

        f = Frame(self.master, height=40, width=150)
        f.pack_propagate(0)
        f.place(x=300, y=650)
        self.speed_combobox = Combobox(f, state='readonly')
        self.speed_combobox['values'] = ('1倍速', '2倍速', '0.5倍速')
        self.speed_combobox.current(0)
        self.speed_combobox.pack()
        self.speed_combobox.bind("<<ComboboxSelected>>", self.calculate_true_time_delay)

        f = Frame(self.master, height=20, width=150)
        f.pack_propagate(0)
        f.place(x=820, y=0)
        self.category_combobox = Combobox(f, state='readonly')
        self.category_combobox.pack()

        f = Frame(self.master, height=40, width=150)
        f.pack_propagate(0)
        f.place(x=450, y=650)
        self.subtitle_combobox = Combobox(f, state='readonly')
        self.subtitle_combobox['values'] = ('无')
        self.subtitle_combobox.current(0)
        self.subtitle_combobox.pack()

        f = Frame(self.master, height=40, width=50)
        f.pack_propagate(0)
        f.place(x=820, y=20)
        self.search_text = Label(f, text='搜索：')
        self.search_text.pack()

        f = Frame(self.master, height=40, width=150)
        f.pack_propagate(0)
        f.place(x=870, y=20)
        self.search_entry = Entry(f)
        self.search_entry.pack()

        f = Frame(self.master, height=40, width=50)
        f.pack_propagate(0)
        f.place(x=1030, y=20)
        self.search_button = Button(f, text="搜索")
        self.search_button["command"] = lambda: self.refreshPlayList(keyword=self.search_entry.get())
        self.search_button.pack()

        f = Frame(self.master, height=300, width=360)
        f.pack_propagate(0)
        f.place(x=820, y=80)
        self.playlist = Listbox(f, width=360, height=300)
        self.playlist.pack()
        self.playlist.bind('<Double-Button-1>', self.pickMovie)

        f = Frame(self.master, height=280, width=360)
        f.pack_propagate(0)
        f.place(x=820, y=400)
        self.historylist = Listbox(f, width=360, height=280)
        self.historylist.pack()

        self.label_frame = Frame(self.master, height=600, width=800)
        self.label_frame.pack_propagate(0)
        self.label_frame.place(x=0, y=0)
        self.label = Label(self.label_frame, width=800, height=600, bg='black')
        # self.label['text'] = ''
        # self.label['fg'] = 'red'
        # self.label['anchor'] = S
        # self.label['compound'] = TOP

        self.label.pack(fill=BOTH, expand=1)

        self.subtitle_frame = Frame(self.master, height=75, width=800)
        self.subtitle_frame.pack_propagate(0)
        self.subtitle_frame.place(x=0, y=525)
        self.subtitlebg = Label(self.subtitle_frame, width=800, height=75, bg='black', fg='white')
        self.subtitlebg.pack(fill=BOTH, expand=1)

        # mycanvas = Canvas(self.master, width=600, height=150, bd=0, highlightthickness=0)
        # mycanvas.create_rectangle(0, 0, 100, 40, fill="green")
        # #mycanvas.pack(side="top", fill="both", expand=True)
        # mycanvas.place(x=100, y=200)
        # # mycanvas.config(bg='')
        # text_canvas = mycanvas.create_text(10, 10, anchor="nw")
        # mycanvas.itemconfig(text_canvas, text="Look no background! Thats new!")


        self.getCategoryList()
        self.refreshPlayList()

        # self.fnt = ImageFont.truetype("C:\Windows\Fonts\simsun.ttc", 18)

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
        self.label_frame.configure(width=self.full_width, height=self.full_height)
        self.subtitle_frame.configure(width=self.full_width)
        self.subtitle_frame.place(y=self.full_height-75)
        # try:
        #     self.updateFrame(self.video_frame_queue.queue[self.video_frame_queue.start_ptr-1][0])
        # except:
        #     pass

    def exitFullScreen(self):
        self.full_screen = False
        self.master.attributes("-fullscreen", False)
        self.label_frame.configure(width=self.origin_width, height=self.origin_height)
        self.subtitle_frame.configure(width=self.origin_width)
        self.subtitle_frame.place(y=self.origin_height-75)
        # try:
        #     self.updateFrame(self.video_frame_queue.queue[self.video_frame_queue.start_ptr-1][0])
        # except:
        #     pass

    def pickMovie(self, event):
        self.memory = ''
        index = self.playlist.curselection()[0]
        movie_name = self.playlist.get(index)
        self.setupMovie(movie_name)


    def initNewMovie(self):
        self.buffering = False
        self.video_frame_queue = FrameQueue(2000)
        self.audio_frame_queue = FrameQueue(2000)
        self.subtitle = {}
        self.has_subtitle = 0
        self.last_frame_no = 0
        self.cur_frame = 0
        self.lock = False
        self.rate = 1
        try:
            self.subtitle_combobox.delete(1)
        except:
            pass
        threading.Thread(target=self.updateMovie).start()
        print("started new")

    def collectVideoFrame(self, image, frame_no):
        self.video_frame_queue.push(image, frame_no)

    def collectAudioFrame(self, sound, frame_no):
        self.audio_frame_queue.push(sound, frame_no)

    def collectSubtitle(self, subtitle, subtitle_no):
        subtitle_info = subtitle.decode('utf-8').split('\n', 1)
        # for i in range(subtitle_no, subtitle_no+int(subtitle_info[0])):
        #     self.subtitle[i] = subtitle_info[1]
        self.subtitle[subtitle_no] = subtitle_info[1]
        self.subtitle[subtitle_no+int(subtitle_info[0])] = ''

    def needBuffering(self):
        video_need = self.video_frame_queue.isEmpty() and self.cur_frame != self.video_frame_count - 1
        audio_need = self.audio_frame_queue.isEmpty() and self.cur_frame != self.video_frame_count - 1
        return video_need or audio_need

    def endBuffering(self):
        # print(self.audio_frame_queue.last(), self.video_frame_queue.last())
        video_end = self.video_frame_queue.reachThresh() or \
                    self.video_frame_queue.last() == self.video_frame_count - 1
        audio_end = self.audio_frame_queue.reachThresh() or \
                    self.audio_frame_queue.last() == self.video_frame_count - 1
        return video_end and audio_end

    def updateFrame(self, img, content=''):
        """Update the image file as video frame in the GUI."""
        l = len(img)
        try:
            img = Image.open(io.BytesIO(img))
        except Exception as e:
            print(str(e), l)
            return
        w = img.size[0]
        h = img.size[1]
        # if not self.full_screen:
        #     nh = self.origin_height
        #     nw = self.origin_width
        # else:
        #     nw = self.full_width
        #     nh = self.full_height - 100
        nw = self.label_frame.winfo_width()
        nh = self.label_frame.winfo_height()
        if w * 3 > h * 4:
            new_size = (nw, nw * h // w)
        else:
            new_size = (nh * w // h, nh)
        img = img.resize(new_size)
        # try:
        #     if content != '':
        #
        #         draw = ImageDraw.Draw(img)
        #         width, height = img.size
        #         text_size = draw.textsize(content, font=self.fnt)
        #         draw.text((width // 2 - text_size[0] // 2, height - text_size[1]), content, fill="#ffffff", font=self.fnt)
        # except:
        #     pass
        photo = ImageTk.PhotoImage(img)
        self.label.configure(image=photo, height=img.size[1])
        self.label.image = photo

    @qt_exception_wrapper
    def updateMovie(self):
        print("updateMovie")
        try:
            while True:
                if self.play_end:
                    break
                start = time.time()
                # print(start)
                if self.state == self.PLAYING:

                    if self.buffering and not self.endBuffering():
                        continue
                    self.buffering = False
                    if not self.video_frame_queue.isEmpty() and not self.audio_frame_queue.isEmpty():
                        # if self.cur_frame >= self.video_frame_count - 1:
                        #     self.pauseMovie()
                        #     while self.PLAYING:
                        #         print("y")
                        #         pass
                        #     continue
                        if self.cur_frame % 10 == 0:
                            self.setSliderPosition(self.cur_frame)
                        c = time.time()
                        if self.audio_frame_queue.top() == self.cur_frame:
                            sound, audio_frame_no = self.audio_frame_queue.pop()
                            threading.Thread(target=self.audio_player.playAudio, args=(sound, self.rate)).start()

                        elif self.audio_frame_queue.top() < self.cur_frame:
                            while True:
                                print(self.audio_frame_queue.top(), self.cur_frame)
                                self.audio_frame_queue.pop()
                                if self.audio_frame_queue.top() > self.cur_frame:
                                    break

                        d = time.time()

                        # print('playsound', round(d - c, 3))
                        if self.video_frame_queue.top() == self.cur_frame:
                            image, frame_no = self.video_frame_queue.pop()

                            if self.subtitle_combobox.current() == 1 and frame_no in self.subtitle.keys():
                                 self.subtitlebg['text'] = self.subtitle[frame_no]

                            self.updateFrame(image)
                        elif self.video_frame_queue.top() < self.cur_frame:
                            while True:
                                self.video_frame_queue.pop()
                                if self.video_frame_queue.top() > self.cur_frame:
                                    break
                        print(self.video_frame_queue.top(), self.audio_frame_queue.top())
                        end = time.time()
                        interval = round(end - start, 3)
                        time_delay = self.modified_time_delay
                        time_delay -= interval
                        print('slleep', time_delay)
                        a = time.time()
                        time.sleep(max(time_delay, 0))
                        b = time.time()
                        self.cur_frame += 1
                        print('actuaaly', round(b - a, 3))
                if self.state == self.PLAYING and self.needBuffering() and not self.buffering:
                    print("found problem")
                    self.buffering = True
                    # self.bufferIcon.setVisible(True)
                    print("found again")
                    # threading.Thread(target=self.bufferShowing).start()
                # elif self.teardownAcked:
                #     assert False
                #     break
            print("ended")
        except Exception as e:
            print("update crashed", str(e))
        try:
            self.audio_player.stream.close()
            self.audio_player.audio.terminate()
        except:
            pass
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
        time_total = self.video_frame_count - 1
        time_cur = time_total * cur // total
        print(time_cur)
        self.cur_frame = time_cur

        self.playMovie(time_cur)

    @qt_exception_wrapper
    def play1(self):
        if self.memory != '':
            self.playMovie(self.memory)
            self.memory = ''
        else:
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

    def refreshPlayList(self, keyword=''):
        if self.playlist.size() > 0:
            self.playlist.delete(0, self.playlist.size()-1)
        play_list = self.retrievePlayList('SEARCH', keyword, self.category_combobox.get())
        print(play_list)
        i = 0
        for movie in play_list:
            self.playlist.insert(i, movie)
            i += 1

    def getCategoryList(self):
        category_list = self.retrievePlayList('CATEGORY')
        category_list.append('所有')
        self.category_combobox['values'] = tuple(category_list)
        self.category_combobox.current(len(category_list)-1)

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
