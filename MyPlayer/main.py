import sys
from extract_frame import FrameExtractor
from pyqt5_ui import PlayerWindow
from PyQt5.QtWidgets import QApplication
from Player import Player
import subprocess
import time

def main_old():
    app = QApplication(sys.argv)
    player_window = PlayerWindow()
    player_window.show()
    frame_extractor = FrameExtractor("test.mp4")
    frame_extractor.next_frame_signal.connect(player_window.getFrame)
    frame_extractor.start()
    # i = 0
    # while True:
    #     frame_extractor.extract(i)
    #     player_window.playFrame(str(i)+".jpg")
    #     if i != 0:
    #         frame_extractor.remove(i-1)
    #     i += 1
    #     time.sleep(0.2)
    sys.exit(app.exec_())

def main():
    time.sleep(1)
    app = QApplication(sys.argv)
    player = Player('127.0.0.1', 10001, 22233, 10004, 10005, 'test.mp4')
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()