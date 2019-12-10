# inherits from the qtdesigner generated files

from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QIcon, QPixmap, QKeyEvent
from PyQt5.QtCore import Qt, QRect, QByteArray, QEvent
from player_ui import *
import time
import threading

from PyQt5.QtWidgets import QMessageBox

def qt_exception_wrapper(func):
    def wrapper(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except Exception as e:
            QMessageBox.information(self, 'Error', 'Meet with Error: ' + str(e),
                QMessageBox.Yes, QMessageBox.Yes)
    return wrapper

class PlayerWindow(QWidget, Ui_Player):
    ORIGIN_SPEED = 0
    DOUBLE_SPEED = 1
    HALF_SPEED = 2
    def __init__(self, parent=None):
        super(PlayerWindow, self).__init__(parent)
        self.setupUi(self)

        self.img_path = None

        # full screen size acquisition
        desktop = QApplication.desktop()
        self.full_size = desktop.screenGeometry()
        self.full_height = self.full_size.height()
        self.full_width = self.full_size.width()
        self.full_geometry = QRect(0, 0, self.full_width, self.full_height)
        self.background_geometry = self.Background.geometry()
        self.origin_geometry = self.Background.geometry()

        # transparent effect
        self.op_half = QtWidgets.QGraphicsOpacityEffect()
        self.op_half.setOpacity(0.5)

        # Button initiation
        self.FullScreenBtn.clicked.connect(lambda: self.setFullScreen())
        self.FullScreenBtn.setFixedWidth(28)
        self.FullScreenBtn.setFixedHeight(28)
        self.FullScreenBtn.setStyleSheet("QPushButton{border-image: url(icons/fullscreen.png)}")
        self.full_screen_btn_geometry = self.FullScreenBtn.geometry()

        self.full_full_screen_btn_geometry = QRect(0, self.full_height-30, 30, 30)

        self.ExitFullScreenBtn.setFixedWidth(28)
        self.ExitFullScreenBtn.setFixedHeight(28)
        self.ExitFullScreenBtn.setStyleSheet("QPushButton{border-image: url(icons/exitfullscreen.png)}")
        self.ExitFullScreenBtn.clicked.connect(lambda: self.exitFullScreen())
        self.ExitFullScreenBtn.setVisible(False)
        self.ExitFullScreenBtn.setGeometry(self.full_width-self.ExitFullScreenBtn.width(),
                                           0,
                                           self.ExitFullScreenBtn.width(),
                                           self.ExitFullScreenBtn.height())

        self.ExitFullScreenBtn.setGraphicsEffect(self.op_half)

        # Slider initiation
        self.Slider.installEventFilter(self)

        self.normal_slider_geometry = self.Slider.geometry()
        self.full_screen_slider_geometry = QRect(0, self.full_height-self.Slider.height(),
                                                 self.full_width, self.Slider.height())

        # PlaySpeedBox initiation
        self.PlaySpeedBox.addItem("1倍速", self.ORIGIN_SPEED)
        self.PlaySpeedBox.addItem("2倍速", self.DOUBLE_SPEED)
        self.PlaySpeedBox.addItem("0.5倍速", self.HALF_SPEED)
        self.play_speed = self.PlaySpeedBox.currentData()
        self.PlaySpeedBox.currentIndexChanged.connect(lambda: self.playSpeedChanged())

        # button initiations
        self.PlayBtn.setFixedWidth(28)
        self.PlayBtn.setFixedHeight(28)
        self.PauseBtn.setFixedWidth(28)
        self.PauseBtn.setFixedHeight(28)

        self.PlayBtn.setStyleSheet("QPushButton{border-image: url(icons/play.png)}")

        self.PauseBtn.setStyleSheet("QPushButton{border-image: url(icons/pause.png)}")

        # Background initiation
        self.playBackground(self.origin_geometry)

        self.bufferIcon = QLabel(self)
        self.bufferIcon.setGeometry(200, 200, 30, 30)
        self.bufferIcon.setFixedHeight(30)
        self.bufferIcon.setFixedWidth(30)
        self.bufferIcon.setVisible(False)
        self.buffering = False

        self.PlayList.itemDoubleClicked.connect(lambda x: self.setupMovie(x.text()))
        # for widget in self.children():
        #     widget.keyPressEvent = self.keyPressEvent

        # threading.Thread(target=self.bufferShowing).start()
        self.origin_menu_geometry = self.horizontalLayout.geometry()
        self.full_menu_geometry = QRect(0, self.full_height-28, self.full_width, 28)

        self.SearchIcon.setStyleSheet("QLabel{border-image: url(icons/search.png)}")
        self.SearchIcon.setFixedWidth(28)
        self.SearchIcon.setFixedHeight(28)
        self.SearchKeyword.returnPressed.connect(lambda: self.refreshPlayList(self.SearchKeyword.text()))
        self.SearchButton.clicked.connect(lambda: self.refreshPlayList(self.SearchKeyword.text()))

        self.SubtitleBox.addItem('无', 0)
        self.SubtitleBox.currentIndexChanged.connect(lambda: self.change_subtitle())
        # self.CategoryComboBox.currentIndexChanged.connect(self.refreshPlayList)

        self.SubtitleText.setStyleSheet("color:red; text-align:right; font-size: 18px; font-weight: bold; font-family: Times New Roman;")

    def change_subtitle(self):
        self.has_subtitle = self.SubtitleBox.currentData()
        if not self.has_subtitle:
            self.SubtitleText.setText('')

    @qt_exception_wrapper
    def playBackground(self, geometry):
        pixmap = QPixmap(geometry.width(), geometry.height())
        pixmap.fill(Qt.black)
        self.Background.setGeometry(geometry)
        self.Background.setPixmap(pixmap)

    @qt_exception_wrapper
    def getFrame(self, img_path):
        self.img_path = img_path
        while self.lock:
            pass
        if self.isFullScreen():
            self.playFrame(self.full_geometry)
        else:
            self.playFrame(self.origin_geometry)

    @qt_exception_wrapper
    def playFrame(self, geometry):
        #print("print")
        self.lock = True
        if self.img_path is None:
            return
        # print(img_path)
        #pixmap = QPixmap(self.img_path)
        #img_bytes = QByteArray(self.img_path)
        pixmap = QPixmap()
        pixmap.loadFromData(self.img_path, "jpg")
        pixmap = pixmap.scaled(geometry.width(), geometry.height(),
                               Qt.KeepAspectRatio, Qt.FastTransformation)

        width = pixmap.width()
        height = pixmap.height()

        middle_x = geometry.x() + (geometry.width() // 2)
        middle_y = geometry.y() + (geometry.height() // 2)
        x = middle_x - (width // 2)
        y = middle_y - (height // 2)
        #print(geometry.width(), width, height, middle_x, x)
        self.Screen.setGeometry(x, y, width, height)
        self.Screen.setPixmap(pixmap)
        self.lock = False

    @qt_exception_wrapper
    def changeScreenSize(self):
        self.screen_width = self.Screen.width()
        self.screen_height = self.Screen.height()

    @qt_exception_wrapper
    def setFullScreen(self):
        if not self.isFullScreen():
            print("beforefullscreen")
            self.showFullScreen()
            self.origin_geometry = self.Background.geometry()
            print("afterfullscreen")
            self.playBackground(self.full_geometry)
            if self.state != self.PLAYING:
                self.playFrame(self.full_geometry)
            print("afterplayframe")

            self.changeScreenSize()

            # self.Slider.setGraphicsEffect(self.op_half)
            print("heeli")
            self.Slider.setGeometry(self.full_screen_slider_geometry)
            print("afterslider")
            # self.FullScreenBtn.setVisible(False)
            # self.PlayBtn.setVisible(False)
            # self.PauseBtn.setVisible(False)
            self.FullScreenBtn.setGeometry(self.full_full_screen_btn_geometry)
            self.PlayList.setVisible(False)
            self.SearchButton.setVisible(False)
            self.SearchIcon.setVisible(False)
            self.SearchKeyword.setVisible(False)
            self.PlaySpeedBox.setVisible(False)
            self.CategoryComboBox.setVisible(False)
            self.CategoryLabel.setVisible(False)
            self.HistoryList.setVisible(False)
            # self.horizontalLayout.setGeometry(self.full_menu_geometry)
            # self.FullScreenBtn.setGraphicsEffect(self.op_half)
            # self.PlayBtn.setGraphicsEffect(self.op_half)
            # self.PauseBtn.setGraphicsEffect(self.op_half)
            print("afterbutton")


            self.ExitFullScreenBtn.setVisible(True)

    @qt_exception_wrapper
    def exitFullScreen(self):
        if self.isFullScreen():
            self.showNormal()
            if self.state != self.PLAYING:
                self.playFrame(self.origin_geometry)
            self.changeScreenSize()
            self.playBackground(self.background_geometry)
            op = QtWidgets.QGraphicsOpacityEffect()
            op.setOpacity(1)
            self.Slider.setGraphicsEffect(op)
            self.Slider.setGeometry(self.normal_slider_geometry)
            # self.FullScreenBtn.setVisible(True)
            # self.PlayBtn.setVisible(True)
            # self.PauseBtn.setVisible(True)
            self.FullScreenBtn.setGeometry(self.full_screen_btn_geometry)
            self.PlayBtn.setGraphicsEffect(op)
            self.PauseBtn.setGraphicsEffect(op)
            self.PlayList.setVisible(True)
            self.SearchButton.setVisible(True)
            self.SearchIcon.setVisible(True)
            self.SearchKeyword.setVisible(True)
            self.HistoryList.setVisible(True)
            self.PlaySpeedBox.setVisible(True)
            self.CategoryComboBox.setVisible(True)
            self.CategoryLabel.setVisible(True)
            # self.horizontalLayout.setGeometry(self.origin_menu_geometry)

            self.ExitFullScreenBtn.setVisible(False)


    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == Qt.Key_Escape:
            self.exitFullScreen()
        if QKeyEvent.key() == Qt.Key_P:
            if self.state == self.PLAYING:
                self.pauseMovie()
            if self.state == self.READY:
                self.playMovie()

    # def event(self, event):
    #     if (event.type() == QEvent.KeyPress) and (event.key() == Qt.Key_Space):
    #         print("yes")
    #         if self.state == self.PLAYING:
    #             self.pauseMovie()
    #         if self.state == self.PAUSE:
    #             self.playMovie()
    #     else:
    #         return QWidget.event(self, event)


    def eventFilter(self, a0: 'QObject', a1: 'QEvent') -> bool:
        if a1.type() == QtCore.QEvent.HoverEnter and self.isFullScreen():
            op = QtWidgets.QGraphicsOpacityEffect()
            op.setOpacity(1)
            self.Slider.setGraphicsEffect(op)
            return False
        if a1.type() == QtCore.QEvent.HoverLeave and self.isFullScreen():
            op = QtWidgets.QGraphicsOpacityEffect()
            op.setOpacity(0.5)
            self.Slider.setGraphicsEffect(op)
            return False
        return False

    @qt_exception_wrapper
    def playSpeedChanged(self):
        self.play_speed = self.PlaySpeedBox.currentData()
        self.calculate_true_time_delay()

    @qt_exception_wrapper
    def bufferShowing(self):
        try:
            i = 0
            while True:
                # print("wula")
                if self.buffering:
                    self.bufferIcon.setStyleSheet("QLabel{border-image: url(icons/buffer%d.png)}" % (i + 1))
                    i += 1
                    i %= 5
                    time.sleep(0.1)
                else:
                    break
        except Exception as e:
            print("show buffer crahsed", str(e))


