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
        Player.resize(821, 692)
        self.Background = QtWidgets.QLabel(Player)
        self.Background.setGeometry(QtCore.QRect(10, 10, 800, 600))
        self.Background.setText("")
        self.Background.setObjectName("Background")
        self.Screen = QtWidgets.QLabel(Player)
        self.Screen.setGeometry(QtCore.QRect(10, 10, 591, 321))
        self.Screen.setObjectName("Screen")
        self.Slider = QtWidgets.QSlider(Player)
        self.Slider.setGeometry(QtCore.QRect(10, 620, 791, 22))
        self.Slider.setOrientation(QtCore.Qt.Horizontal)
        self.Slider.setObjectName("Slider")
        self.horizontalLayoutWidget = QtWidgets.QWidget(Player)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(10, 649, 801, 31))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.FullScreenBtn = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.FullScreenBtn.setObjectName("FullScreenBtn")
        self.horizontalLayout.addWidget(self.FullScreenBtn)
        self.PlayBtn = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.PlayBtn.setObjectName("PlayBtn")
        self.horizontalLayout.addWidget(self.PlayBtn)
        self.PauseBtn = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.PauseBtn.setObjectName("PauseBtn")
        self.horizontalLayout.addWidget(self.PauseBtn)
        self.ExitFullScreenBtn = QtWidgets.QPushButton(Player)
        self.ExitFullScreenBtn.setGeometry(QtCore.QRect(720, 0, 93, 28))
        self.ExitFullScreenBtn.setText("")
        self.ExitFullScreenBtn.setObjectName("ExitFullScreenBtn")

        self.retranslateUi(Player)
        QtCore.QMetaObject.connectSlotsByName(Player)

    def retranslateUi(self, Player):
        _translate = QtCore.QCoreApplication.translate
        Player.setWindowTitle(_translate("Player", "Form"))
        self.Screen.setText(_translate("Player", "TextLabel"))
        self.FullScreenBtn.setText(_translate("Player", "Fullscreen"))
        self.PlayBtn.setText(_translate("Player", "Play"))
        self.PauseBtn.setText(_translate("Player", "Pause"))
