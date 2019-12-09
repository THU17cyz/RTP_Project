import sys
from PyQt5.QtWidgets import QApplication
from Player import Player
import time


def main():
    time.sleep(1)
    app = QApplication(sys.argv)
    player = Player('127.0.0.1', 10001, 22233, 10004, 10005, 'test.mp4')
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
