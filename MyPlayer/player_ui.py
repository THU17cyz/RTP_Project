# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'player_ui.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Player(object):
    def setupUi(self, Player):
        Player.setObjectName("Player")
        Player.resize(1200, 722)
        self.Background = QtWidgets.QLabel(Player)
        self.Background.setGeometry(QtCore.QRect(10, 10, 840, 630))
        self.Background.setText("")
        self.Background.setObjectName("Background")
        self.Screen = QtWidgets.QLabel(Player)
        self.Screen.setGeometry(QtCore.QRect(10, 10, 591, 321))
        self.Screen.setObjectName("Screen")
        self.Slider = QtWidgets.QSlider(Player)
        self.Slider.setGeometry(QtCore.QRect(10, 650, 840, 20))
        self.Slider.setOrientation(QtCore.Qt.Horizontal)
        self.Slider.setObjectName("Slider")
        self.horizontalLayoutWidget = QtWidgets.QWidget(Player)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(10, 680, 841, 31))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.FullScreenBtn = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.FullScreenBtn.sizePolicy().hasHeightForWidth())
        self.FullScreenBtn.setSizePolicy(sizePolicy)
        self.FullScreenBtn.setText("")
        self.FullScreenBtn.setObjectName("FullScreenBtn")
        self.horizontalLayout.addWidget(self.FullScreenBtn)
        self.PlayBtn = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.PlayBtn.setText("")
        self.PlayBtn.setObjectName("PlayBtn")
        self.horizontalLayout.addWidget(self.PlayBtn)
        self.PauseBtn = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.PauseBtn.setText("")
        self.PauseBtn.setObjectName("PauseBtn")
        self.horizontalLayout.addWidget(self.PauseBtn)
        self.PlaySpeedBox = QtWidgets.QComboBox(self.horizontalLayoutWidget)
        self.PlaySpeedBox.setObjectName("PlaySpeedBox")
        self.horizontalLayout.addWidget(self.PlaySpeedBox)
        self.ExitFullScreenBtn = QtWidgets.QPushButton(Player)
        self.ExitFullScreenBtn.setGeometry(QtCore.QRect(720, 0, 93, 28))
        self.ExitFullScreenBtn.setText("")
        self.ExitFullScreenBtn.setObjectName("ExitFullScreenBtn")
        self.PlayList = QtWidgets.QListWidget(Player)
        self.PlayList.setGeometry(QtCore.QRect(870, 10, 311, 691))
        self.PlayList.setObjectName("PlayList")

        self.retranslateUi(Player)
        QtCore.QMetaObject.connectSlotsByName(Player)

    def retranslateUi(self, Player):
        _translate = QtCore.QCoreApplication.translate
        Player.setWindowTitle(_translate("Player", "Form"))
        self.Screen.setText(_translate("Player", "TextLabel"))
