import sys
from PyQt5.QtWidgets import QApplication
from Player import Player
import time
from tkinter import *
import tkinter.messagebox as tkMessageBox
from PIL import Image, ImageTk


def main(tk):
    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook
    time.sleep(1)
    # app = QApplication(sys.argv)
    player = Player(tk, '127.0.0.1', 10001, 22233, 10004, 10005, 'test.mp4')
    # sys.exit(app.exec_())


if __name__ == "__main__":
    tk = Tk()
    main(tk)
    tk.mainloop()
