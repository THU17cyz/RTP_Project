import io
import os
import time
import threading

from tkinter import *
import tkinter.messagebox as tkMessageBox
from tkinter.ttk import Combobox

from PIL import Image, ImageTk, ImageFile

from audio_player import AudioPlayer
from Client import Client
import ctypes

ImageFile.LOAD_TRUNCATED_IMAGES = True

winmm = ctypes.WinDLL('winmm')
winmm.timeBeginPeriod(1)


class FrameQueue:
    """
    this class acts as a buffer
    """
    def __init__(self, capacity, thresh=100, full_thresh=1000, safe_thresh=500):
        self.capacity = capacity  # maximum length of queue
        self.queue = [None] * self.capacity  # stores information
        self.length = 0  # length
        self.start_ptr = 0  # start position
        self.end_ptr = 0  # end position
        self.thresh = thresh  # a movie can be played if length > thresh
        self.full_thresh = full_thresh  # server speed should be controlled if length > full_thresh
        self.safe_thresh = safe_thresh  # server speed should be unconstrained if length < safe_thresh

    def isEmpty(self):
        return self.length == 0

    def isFull(self):
        return self.length == self.capacity

    def reachThresh(self):
        return self.length > self.thresh

    def almostFull(self):
        return self.length > self.full_thresh

    def safeNow(self):
        return self.length <= self.safe_thresh

    # enter queue
    def push(self, frame, frame_no):
        self.queue[self.end_ptr] = (frame, frame_no)
        self.end_ptr += 1
        self.end_ptr %= self.capacity
        self.length += 1

    # leave queue and dump the data
    def pop(self):
        frame, frame_no = self.queue[self.start_ptr]
        self.queue[self.start_ptr] = None
        self.start_ptr += 1
        self.start_ptr %= self.capacity
        self.length -= 1
        return frame, frame_no

    # get the first element
    def top(self):
        if self.length == 0:
            return 99999999
        return self.queue[self.start_ptr][1]

    # skip to end position, releasing the data skipped
    def jump(self):
        if self.end_ptr > self.start_ptr:
            for i in range(self.start_ptr, self.end_ptr):
                self.queue[i] = None
        else:
            for i in range(self.start_ptr, self.capacity):
                self.queue[i] = None
            for i in range(0, self.end_ptr):
                self.queue[i] = None
        self.start_ptr = self.end_ptr
        self.length = 0

    # get the frame number of the last element
    def last(self):
        if self.start_ptr == self.end_ptr:
            return None
        last = self.end_ptr - 1
        if last == -1:
            last = self.capacity - 1
        return self.queue[last][1]


class Player(Client):
    """
    the Player class, inherits from Client
    combines GUI and logic
    """
    def __init__(self, master, server_addr, server_rtsp_port, server_plp_port, rtp_port, plp_port):
        Client.__init__(self, server_addr, server_rtsp_port, server_plp_port, rtp_port, plp_port)
        self.play_end = False  # if a video is completely played, set this to True
        self.play_speed = 0  # play speed option
        self.cur_frame = 0  # current frame played
        self.record_file = 'record/record.txt'  # where to store the record file
        self.play_record = {}  # play record, used for transmission resume

        # initiates GUI
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()

        # reads record
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
                if tkMessageBox.askyesno("提示", "是否加载上次观看的位置?"):
                    self.setupMovie(last_movie)
                    frame_memory = int(frame_memory)
                    self.cur_frame = frame_memory
                    self.memory = frame_memory
            else:
                self.memory = ''
        else:
            self.memory = ''

    def createWidgets(self):
        """
        Build GUI.
        """
        self.full_screen = False

        self.origin_height = 600
        self.origin_width = 800

        self.full_height = self.master.winfo_screenheight()
        self.full_width = self.master.winfo_screenwidth()

        self.master.title("这是一个播放器")
        self.master.geometry('1200x700')
        self.master.resizable(0, 0)
        self.master.bind_all('<KeyPress>', self.key_press)

        # some icons
        full_icon = Image.open('icons/fullscreen.png')
        full_icon = full_icon.resize((25, 25))
        full_icon = ImageTk.PhotoImage(full_icon)
        play_icon = Image.open('icons/play.png')
        play_icon = play_icon.resize((25, 25))
        play_icon = ImageTk.PhotoImage(play_icon)
        pause_icon = Image.open('icons/pause.png')
        pause_icon = pause_icon.resize((25, 25))
        pause_icon = ImageTk.PhotoImage(pause_icon)

        # buttons play, fullscreen and pause
        f1 = Frame(self.master, height=40, width=65)
        f1.pack_propagate(0)  # don't shrink
        f1.place(x=5, y=650)
        self.fullscreen = Button(f1, width=65, height=40, image=full_icon, text='全屏', font=15, compound=LEFT)
        self.fullscreen.image = full_icon
        self.fullscreen['command'] = self.setFullScreen
        self.fullscreen.pack()

        f3 = Frame(self.master, height=40, width=65)
        f3.pack_propagate(0)
        f3.place(x=75, y=650)
        self.play = Button(f3, width=65, height=40, image=play_icon, text='播放', font=15, compound=LEFT)
        self.play.image = play_icon
        self.play['command'] = self.play1
        self.play.pack()

        f2 = Frame(self.master, height=40, width=65)
        f2.pack_propagate(0)
        f2.place(x=145, y=650)
        self.pause = Button(f2, width=65, height=40, image=pause_icon, text='暂停', font=15, compound=LEFT)
        self.pause.image = pause_icon
        self.pause['command'] = self.pauseMovie
        self.pause.pack()

        # slider
        f2 = Frame(self.master, height=40, width=800)
        f2.pack_propagate(0)
        f2.place(x=0, y=600)
        self.slider = Scale(f2, orient=HORIZONTAL, length=800)
        self.slider.pack(fill=BOTH, expand=1)
        self.slider['state'] = 'disabled'
        self.slider.bind("<ButtonPress>", self.sliderPressEvent)
        self.slider.bind("<ButtonRelease>", self.sliderReleaseEvent)

        # three comboboxes
        f = Frame(self.master, height=40, width=150)
        f.pack_propagate(0)
        f.place(x=215, y=650)
        self.speed_combobox = Combobox(f, state='readonly')
        self.speed_combobox['values'] = ('1倍速', '2倍速', '0.5倍速')
        self.speed_combobox.current(0)
        self.speed_combobox.pack(fill=BOTH, expand=1)
        self.speed_combobox.bind("<<ComboboxSelected>>", self.calculate_true_time_delay)

        f = Frame(self.master, height=40, width=150)
        f.pack_propagate(0)
        f.place(x=370, y=650)
        self.subtitle_combobox = Combobox(f, state='readonly')
        self.subtitle_combobox['values'] = ('无')
        self.subtitle_combobox.current(0)
        self.subtitle_combobox.pack(fill=BOTH, expand=1)

        f = Frame(self.master, height=40, width=150)
        f.pack_propagate(0)
        f.place(x=525, y=650)
        self.quality_combobox = Combobox(f, state='readonly')
        self.quality_combobox['values'] = ('正常', '压缩2倍', '压缩4倍')
        self.quality_combobox.current(0)
        self.quality_combobox.pack(fill=BOTH, expand=1)
        self.quality_combobox.bind("<<ComboboxSelected>>", self.qualityControl)

        # search part
        f = Frame(self.master, height=30, width=50)
        f.pack_propagate(0)
        f.place(x=820, y=5)
        self.category_text = Label(f, text='类别：')
        self.category_text.pack(fill=BOTH, expand=1)

        f = Frame(self.master, height=30, width=305)
        f.pack_propagate(0)
        f.place(x=875, y=5)
        self.category_combobox = Combobox(f, state='readonly')
        self.category_combobox.pack(fill=BOTH, expand=1)

        f = Frame(self.master, height=30, width=50)
        f.pack_propagate(0)
        f.place(x=820, y=40)
        self.search_text = Label(f, text='搜索：')
        self.search_text.pack(fill=BOTH, expand=1)

        f = Frame(self.master, height=30, width=250)
        f.pack_propagate(0)
        f.place(x=875, y=40)
        self.search_entry = Entry(f)
        self.search_entry.pack(fill=BOTH, expand=1)

        f = Frame(self.master, height=30, width=50)
        f.pack_propagate(0)
        f.place(x=1130, y=40)
        self.search_button = Button(f, text="搜索")
        self.search_button["command"] = lambda: self.refreshPlayList(keyword=self.search_entry.get())
        self.search_button.pack(fill=BOTH, expand=1)

        f = Frame(self.master, height=320, width=360)
        f.pack_propagate(0)
        f.place(x=820, y=80)
        self.playlist = Listbox(f, width=360, height=320)
        self.playlist.pack()
        self.playlist.bind('<Double-Button-1>', self.pickMovie)

        f = Frame(self.master, height=280, width=360)
        f.pack_propagate(0)
        f.place(x=820, y=410)
        self.historylist = Listbox(f, width=360, height=280)
        self.historylist.pack()
        self.historylist.bind('<Double-Button-1>', self.pickMovie)

        # label that displays video
        self.label_frame = Frame(self.master, height=600, width=800)
        self.label_frame.pack_propagate(0)
        self.label_frame.place(x=5, y=5)
        self.label = Label(self.label_frame, width=800, height=600, bg='black')
        self.label.pack(fill=BOTH, expand=1)

        # subtitle blackboard, also displays some messages
        self.subtitle_frame = Frame(self.master, height=50, width=800)
        self.subtitle_frame.pack_propagate(0)
        self.subtitle_frame.place(x=5, y=555)
        self.subtitlebg = Label(self.subtitle_frame, width=800, height=50, bg='black', fg='white')
        self.subtitlebg.pack(fill=BOTH, expand=1)

        self.getCategoryList()
        self.refreshPlayList()

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

    # enter and exit full screen mode
    def setFullScreen(self):
        self.full_screen = True
        self.master.attributes("-fullscreen", True)
        self.label_frame.configure(width=self.full_width, height=self.full_height)
        self.label_frame.place(x=0, y=0)
        self.subtitle_frame.configure(width=self.full_width)
        self.subtitle_frame.place(x=0, y=self.full_height-50)

    def exitFullScreen(self):
        self.full_screen = False
        self.master.attributes("-fullscreen", False)
        self.label_frame.configure(width=self.origin_width, height=self.origin_height)
        self.label_frame.place(x=5, y=5)
        self.subtitle_frame.configure(width=self.origin_width)
        self.subtitle_frame.place(x=5, y=self.origin_height-45)

    # pick a movie to start when double clicking a list item
    def pickMovie(self, event):
        self.memory = ''
        index = event.widget.curselection()[0]
        movie_name = event.widget.get(index)
        if movie_name != self.movie_name:
            self.setupMovie(movie_name)

    # initializes a new movie session
    def initNewMovie(self):
        self.buffering = False
        self.buffer_control = False
        self.video_frame_queue = FrameQueue(1500)
        self.audio_frame_queue = FrameQueue(1500)
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

    # three functions that collect video/audio/subtitle data
    def collectVideoFrame(self, image, frame_no):
        self.video_frame_queue.push(image, frame_no)

    def collectAudioFrame(self, sound, frame_no):
        self.audio_frame_queue.push(sound, frame_no)

    def collectSubtitle(self, subtitle, subtitle_no):
        subtitle_info = subtitle.decode('utf-8').split('\n', 1)
        self.subtitle[subtitle_no] = subtitle_info[1]
        self.subtitle[subtitle_no+int(subtitle_info[0])] = ''

    # four functions that judges whether buffer satisfies some condition
    def needBuffering(self):
        video_need = self.video_frame_queue.isEmpty() and self.cur_frame != self.video_frame_count
        audio_need = self.audio_frame_queue.isEmpty() and self.cur_frame != self.video_frame_count
        return video_need or audio_need

    def endBuffering(self):
        video_end = self.video_frame_queue.reachThresh() or \
                    self.video_frame_queue.last() == self.video_frame_count - 1
        audio_end = self.audio_frame_queue.reachThresh() or \
                    self.audio_frame_queue.last() == self.video_frame_count - 1
        return video_end and audio_end

    def bufferAlmostFull(self):
        video_full = self.video_frame_queue.almostFull()
        audio_full = self.audio_frame_queue.almostFull()
        return video_full or audio_full

    def bufferNowSafe(self):
        video_safe = self.video_frame_queue.safeNow()
        audio_safe = self.audio_frame_queue.safeNow()
        return video_safe and audio_safe

    # Update the image file as video frame in the GUI.
    def updateFrame(self, img, content=''):
        l = len(img)
        try:
            img = Image.open(io.BytesIO(img))
        except Exception as e:
            print(str(e), l)
            return
        w = img.size[0]
        h = img.size[1]
        nw = self.label_frame.winfo_width()
        nh = self.label_frame.winfo_height()
        if w * 3 > h * 4:
            new_size = (nw, nw * h // w)
        else:
            new_size = (nh * w // h, nh)
        img = img.resize(new_size)
        photo = ImageTk.PhotoImage(img)
        self.label.configure(image=photo, height=img.size[1])
        self.label.image = photo

    # thread that updates video/audio/subtitle
    def updateMovie(self):
        try:
            while True:
                # play reaches an end
                if self.play_end:
                    break
                start = time.time()
                if self.bufferAlmostFull():
                    self.sendRtspRequest(self.SET_PARAMETER, 'buffer_full', 'true')
                    self.buffer_control = True
                if self.buffer_control and self.bufferNowSafe():
                    self.sendRtspRequest(self.SET_PARAMETER, 'buffer_full', 'false')
                    self.buffer_control = False
                if self.state == self.PLAYING:
                    # print(self.video_frame_queue.length)
                    if self.cur_frame == self.video_frame_count:
                        continue
                    if self.buffering and not self.endBuffering():
                        continue
                    elif self.buffering:
                        self.subtitlebg['text'] = ''
                    self.buffering = False
                    if not self.video_frame_queue.isEmpty() and not self.audio_frame_queue.isEmpty():
                        # if self.cur_frame >= self.video_frame_count - 1:
                        #     self.pauseMovie()
                        #     while self.PLAYING:
                        #         print("y")
                        #         pass
                        #     continue
                        if self.cur_frame % 10 == 0 or self.cur_frame == self.video_frame_count - 1:
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
                        #print(self.video_frame_queue.top(), self.audio_frame_queue.top())
                        end = time.time()
                        interval = round(end - start, 3)
                        time_delay = self.modified_time_delay
                        time_delay -= interval
                        #print('slleep', time_delay)
                        a = time.time()
                        time.sleep(max(time_delay, 0))
                        b = time.time()
                        self.cur_frame += 1
                        #print('actuaaly', round(b - a, 3))
                if self.state == self.PLAYING and self.needBuffering() and not self.buffering \
                        and self.cur_frame != self.video_frame_count:
                    print("found problem")
                    self.buffering = True
                    self.subtitlebg['text'] = '正在缓冲，请稍候...'
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

    def sliderPressEvent(self, event):
        if self.slider['state'] == 'disabled':
            return
        self.pauseMovie()

    def sliderReleaseEvent(self, event):
        if self.slider['state'] == 'disabled':
            return
        self.video_frame_queue.jump()
        self.audio_frame_queue.jump()
        total = 100
        cur = self.slider.get()
        time_total = self.video_frame_count - 1
        time_cur = time_total * cur // total
        self.cur_frame = time_cur
        self.playMovie(time_cur)

    def setSliderPosition(self, frame_no):
        # value = self.frameNbr * self.Slider.maximum() // self.video_frame_count
        value = frame_no * 100 // (self.video_frame_count - 1)
        self.slider.set(value)

    def play1(self):
        if self.subtitlebg['text'] == '资源加载完成。':
            self.subtitlebg['text'] = ''
        if self.memory != '':
            self.playMovie(self.memory)
            self.memory = ''
        else:
            self.playMovie()

    # send command to control video quality
    def qualityControl(self, event):
        self.quality = int(self.speed_combobox.current())
        if self.quality == 0:
            self.sendRtspRequest(self.SET_PARAMETER, 'compress', '1')
        elif self.quality == 1:
            self.sendRtspRequest(self.SET_PARAMETER, 'compress', '2')
        else:
            self.sendRtspRequest(self.SET_PARAMETER, 'compress', '4')

    # calculate true time delay according to play speed
    def calculate_true_time_delay(self, event):
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

    # refresh playlist
    def refreshPlayList(self, keyword=''):
        if self.playlist.size() > 0:
            self.playlist.delete(0, self.playlist.size()-1)
        play_list = self.retrievePlayList('SEARCH', keyword, self.category_combobox.get())
        print(play_list)
        i = 0
        for movie in play_list:
            self.playlist.insert(i, movie)
            i += 1

    # get category list
    def getCategoryList(self):
        category_list = self.retrievePlayList('CATEGORY')
        category_list.append('所有')
        self.category_combobox['values'] = tuple(category_list)
        self.category_combobox.current(len(category_list)-1)

    # Handler on explicitly closing the GUI window.
    def handler(self):
        self.pauseMovie()
        if tkMessageBox.askokcancel("提示", "确定要退出吗？"):
            self.exitClient()
        else:
            self.playMovie()


