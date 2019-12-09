# inherits from the qtdesigner generated files

from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QRect, QByteArray
from player_ui import *
import time
import threading


class PlayerWindow(QWidget, Ui_Player):
    ORIGIN_SPEED = 0
    DOUBLE_SPEED = 1
    HALF_SPEED = 2
    def __init__(self, parent=None):
        super(PlayerWindow, self).__init__(parent)
        self.setupUi(self)
        # self.screen_width = self.Background.width()
        # self.screen_height = self.Background.height()
        # self.middle_x = (self.screen_width // 2) + self.Background.x()
        # self.middle_y = (self.screen_height // 2) + self.Background.y()

        self.img_path = None

        # full screen size acquisition
        self.desktop = QApplication.desktop()
        self.full_size = self.desktop.screenGeometry()
        self.full_height = self.full_size.height()
        self.full_width = self.full_size.width()
        self.full_geometry = QRect(0, 0, self.full_width, self.full_height)

        self.background_geometry = self.Background.geometry()
        self.last_geometry = self.Background.geometry()

        # Button initiation
        self.FullScreenBtn.clicked.connect(self.setFullScreen)
        self.FullScreenBtn.setFixedWidth(28)
        self.FullScreenBtn.setFixedHeight(28)
        self.FullScreenBtn.setStyleSheet("QPushButton{border-image: url(icons/fullscreen.png)}")
        self.full_screen_btn_geometry = self.FullScreenBtn.geometry()
        self.full_full_screen_btn_geometry = QRect(0, self.full_height-30, 30, 30)

        self.ExitFullScreenBtn.setFixedWidth(28)
        self.ExitFullScreenBtn.setFixedHeight(28)
        self.ExitFullScreenBtn.setStyleSheet("QPushButton{border-image: url(icons/exitfullscreen.png)}")
        self.ExitFullScreenBtn.clicked.connect(self.exitFullScreen)
        self.ExitFullScreenBtn.setVisible(False)
        self.ExitFullScreenBtn.setGeometry(self.full_width-self.ExitFullScreenBtn.width(),
                                           0,
                                           self.ExitFullScreenBtn.width(),
                                           self.ExitFullScreenBtn.height())
        op = QtWidgets.QGraphicsOpacityEffect()
        op.setOpacity(0.5)
        self.ExitFullScreenBtn.setGraphicsEffect(op)

        # Slider initiation
        self.Slider.installEventFilter(self)
        # self.Slider.raise_()
        self.normal_slider_geometry = self.Slider.geometry()
        self.full_screen_slider_geometry = QRect(0, self.full_height-self.Slider.height(),
                                                 self.full_width, self.Slider.height())

        # PlaySpeedBox initiation
        self.PlaySpeedBox.addItem("1倍速", self.ORIGIN_SPEED)
        self.PlaySpeedBox.addItem("2倍速", self.DOUBLE_SPEED)
        self.PlaySpeedBox.addItem("0.5倍速", self.HALF_SPEED)
        self.play_speed = self.PlaySpeedBox.currentData()
        self.PlaySpeedBox.currentIndexChanged.connect(self.playSpeedChanged)

        self.PlayBtn.setFixedWidth(28)
        self.PlayBtn.setFixedHeight(28)
        self.PauseBtn.setFixedWidth(28)
        self.PauseBtn.setFixedHeight(28)

        self.PlayBtn.setStyleSheet("QPushButton{border-image: url(icons/play.png)}")

        self.PauseBtn.setStyleSheet("QPushButton{border-image: url(icons/pause.png)}")

        # Background initiation
        self.playBackground(self.last_geometry)

        self.bufferIcon = QLabel(self)
        self.bufferIcon.setGeometry(200, 200, 30, 30)
        self.bufferIcon.setFixedHeight(30)
        self.bufferIcon.setFixedWidth(30)
        self.bufferIcon.setVisible(False)
        self.buffering = False

        self.PlayList.itemDoubleClicked.connect(self.foo)

        # threading.Thread(target=self.bufferShowing).start()
    def foo(self, item):
        print(item.text())
    def playBackground(self, geometry):
        pixmap = QPixmap(geometry.width(), geometry.height())
        pixmap.fill(Qt.black)
        self.Background.setGeometry(geometry)
        self.Background.setPixmap(pixmap)

    def getFrame(self, img_path):
        self.img_path = img_path
        while self.lock:
            pass
        if self.isFullScreen():
            self.playFrame(self.full_geometry)
        else:
            self.playFrame(self.last_geometry)

    def playFrame(self, geometry):
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

    def changeScreenSize(self):
        self.screen_width = self.Screen.width()
        self.screen_height = self.Screen.height()

    def setFullScreen(self):
        if not self.isFullScreen():
            print("beforefullscreen")
            self.showFullScreen()
            self.last_geometry = self.Background.geometry()
            print("afterfullscreen")
            self.playBackground(self.full_geometry)
            if self.state != self.PLAYING:
                self.playFrame(self.full_geometry)
            print("afterplayframe")

            self.changeScreenSize()
            op = QtWidgets.QGraphicsOpacityEffect()
            op.setOpacity(0.5)
            self.Slider.setGraphicsEffect(op)
            self.Slider.setGeometry(self.full_screen_slider_geometry)
            print("afterslider")
            # self.FullScreenBtn.setVisible(False)
            # self.PlayBtn.setVisible(False)
            # self.PauseBtn.setVisible(False)
            self.FullScreenBtn.setGeometry(self.full_full_screen_btn_geometry)
            self.FullScreenBtn.setGraphicsEffect(op)
            self.PlayBtn.setGraphicsEffect(op)
            self.PauseBtn.setGraphicsEffect(op)
            print("afterbutton")


            self.ExitFullScreenBtn.setVisible(True)

    def exitFullScreen(self):
        if self.isFullScreen():
            self.showNormal()
            if self.state != self.PLAYING:
                self.playFrame(self.last_geometry)
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

            self.ExitFullScreenBtn.setVisible(False)

    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == Qt.Key_Escape:
            self.exitFullScreen()


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

    def showSlider(self):
        self.Slider.setVisible(True)

    def playSpeedChanged(self):
        self.play_speed = self.PlaySpeedBox.currentData()
        self.calculate_true_time_delay()

    def bufferShowing(self):
        i = 0
        while True:
            if self.buffering:
                # pixmap = QPixmap("icons/buffer"+str(i+1)+'.png')
                # self.bufferIcon.setPixmap(pixmap)
                self.bufferIcon.setStyleSheet("QLabel{border-image: url(icons/buffer%d.png)}" % (i+1))
                #print("hr")
                i += 1
                i %= 5
                time.sleep(0.1)
            else:
                break


