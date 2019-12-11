import sys
from Player import Player
from tkinter import *


def main(tk):
    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook
    if len(sys.argv) == 5:
        server_rtsp_port = sys.argv[1]
        server_plp_port = sys.argv[2]
        rtp_port = sys.argv[3]
        plp_port = sys.argv[4]
    else:
        server_rtsp_port = 10001
        server_plp_port = 22233
        rtp_port = 10004
        plp_port = 10005

    player = Player(tk, server_rtsp_port, server_plp_port, rtp_port, plp_port)


if __name__ == "__main__":
    tk = Tk()
    main(tk)
    tk.mainloop()
