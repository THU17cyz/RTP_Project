# inherits from the qtdesigner generated files

from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QRect, QByteArray
from player_ui import *


class PlayerWindow(QWidget, Ui_Player):

    def __init__(self, parent=None):
        super(PlayerWindow, self).__init__(parent)
        self.setupUi(self)
        # self.screen_width = self.Background.width()
        # self.screen_height = self.Background.height()
        # self.middle_x = (self.screen_width // 2) + self.Background.x()
        # self.middle_y = (self.screen_height // 2) + self.Background.y()

        # self.img_path = None

        # full screen size acquisition
        self.desktop = QApplication.desktop()
        self.full_size = self.desktop.screenGeometry()
        self.full_height = self.full_size.height()
        self.full_width = self.full_size.width()
        self.full_geometry = QRect(0, 0, self.full_width, self.full_height)

        self.last_geometry = self.Background.geometry()

        # Button initiation
        self.FullScreenBtn.clicked.connect(self.setFullScreen)
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
        self.full_screen_slider_geometry = QRect(0, self.full_height-self.Slider.height(),
                                                 self.full_width, self.Slider.height())


        # Background initiation
        self.playBackground(self.last_geometry)

    def playBackground(self, geometry):
        pixmap = QPixmap(geometry.width(), geometry.height())
        pixmap.fill(Qt.black)
        self.Background.setGeometry(geometry)
        self.Background.setPixmap(pixmap)

    def getFrame(self, img_path):
        self.img_path = img_path
        if self.isFullScreen():
            self.playFrame(self.full_geometry)
        else:
            self.playFrame(self.last_geometry)

    def playFrame(self, geometry):
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

    def changeScreenSize(self):
        self.screen_width = self.Screen.width()
        self.screen_height = self.Screen.height()

    def setFullScreen(self):
        if not self.isFullScreen():
            self.showFullScreen()
            self.last_geometry = self.Screen.geometry()

            self.playFrame(self.full_geometry)
            self.playBackground(self.full_geometry)

            self.changeScreenSize()
            op = QtWidgets.QGraphicsOpacityEffect()
            op.setOpacity(0)
            self.Slider.setGraphicsEffect(op)
            self.Slider.setGeometry(self.full_screen_slider_geometry)
            self.FullScreenBtn.setVisible(False)
            self.PlayBtn.setVisible(False)
            self.PauseBtn.setVisible(False)

            self.ExitFullScreenBtn.setVisible(True)

    def exitFullScreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.playFrame(self.last_geometry)
            self.changeScreenSize()
            self.playBackground(self.last_geometry)
            op = QtWidgets.QGraphicsOpacityEffect()
            op.setOpacity(1)
            self.Slider.setGraphicsEffect(op)
            self.FullScreenBtn.setVisible(True)
            self.PlayBtn.setVisible(True)
            self.PauseBtn.setVisible(True)

            self.ExitFullScreenBtn.setVisible(False)

    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == Qt.Key_Escape:
            self.exitFullScreen()


    def eventFilter(self, a0: 'QObject', a1: 'QEvent') -> bool:
        if a1.type() == QtCore.QEvent.HoverEnter and self.isFullScreen():
            op = QtWidgets.QGraphicsOpacityEffect()
            op.setOpacity(1)
            self.Slider.setGraphicsEffect(op)
            return True
        if a1.type() == QtCore.QEvent.HoverLeave and self.isFullScreen():
            op = QtWidgets.QGraphicsOpacityEffect()
            op.setOpacity(0)
            self.Slider.setGraphicsEffect(op)
            return True
        return False

    def showSlider(self):
        self.Slider.setVisible(True)


