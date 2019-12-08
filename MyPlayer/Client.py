from tkinter import *
import tkinter.messagebox as tkMessageBox
from PIL import Image, ImageTk
from PyQt5.QtWidgets import QMessageBox

from pyqt5_ui import PlayerWindow
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    DESCRIBE = 4

    # Initiation..
    def __init__(self, serveraddr, serverport, server_plp_port, rtpport, plp_port, movie_name):
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.server_plp_port = int(server_plp_port)
        self.rtpPort = int(rtpport)
        self.plp_port = int(plp_port)
        self.movie_name = movie_name
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.setupMovie(movie_name)

        self.frameNbr = 0
        self.video_frame_count = 0
        self.video_fps = 0
        self.time_delay = 0
        self.modified_time_delay = 0

    def retrievePlayList(self, keyword=''):
        plp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        plp_socket.settimeout(1)
        plp_socket.bind(("", self.plp_port))
        addr = (self.serverAddr, self.server_plp_port)
        if keyword == '':
            plp_socket.sendto('LIST'.encode('utf-8'), addr)
        else:
            cmd = 'SEARCH ' + keyword
            plp_socket.sendto(cmd.encode('utf-8'), addr)
        response, addr = plp_socket.recvfrom(8192)
        play_list = response.decode().split('\n')
        plp_socket.close()
        return play_list


    def setupMovie(self, movie_name):
        """Setup button handler."""
        if self.state == self.INIT:
            self.movie_name = movie_name
            self.sendRtspRequest(self.SETUP, movie_name)


    def exitAttempt(self):
        if self.state != self.PLAYING:
            self.exitClient()
        else:
            self.pauseMovie()
            do_exit = QMessageBox.information(None, 'Quit?', 'Are you sure you want to quit?',
                                              QMessageBox.Yes | QMessageBox.No)
            if do_exit == QMessageBox.Yes:
                self.exitClient()
            else:
                self.playMovie()



    def exitClient(self):
        self.sendRtspRequest(self.TEARDOWN)


    def pauseMovie(self):
        """Pause button handler."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self, pos=-1):
        """Play button handler."""
        if self.state == self.READY:
            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            if pos == -1:
                self.sendRtspRequest(self.PLAY)
            else:
                self.sendRtspRequest(self.PLAY, pos)

    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                data = self.rtpSocket.recv(80000)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    self.frameNbr = rtpPacket.seqNum()
                    #print("Current Seq Num: " + str(currFrameNbr))
                    #if currFrameNbr > self.frameNbr: # Discard the late packet
                    # self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
                    if rtpPacket.payloadType() == 26:
                        self.collectFrame(rtpPacket.getPayload(), self.frameNbr)
                    elif rtpPacket.payloadType() == 10:
                        self.collectAudioFrame(rtpPacket.getPayload(), self.frameNbr)

            except:
                # Stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    break

                # Upon receiving ACK for TEARDOWN request,
                # close the RTP socket
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()

        return cachename

    def collectFrame(self, image):
        pass

    def collectAudioFrame(self, sound):
        pass

    def updateMovie(self):
        """Update the image file as video frame in the GUI."""
        # img = Image.open(imageFile)
        # photo = ImageTk.PhotoImage(img)
        # self.label.configure(image = photo, height=img.size[1])
        # self.label.image = photo
        pass

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            tkMessageBox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)

    def sendRtspRequest(self, requestCode, *args):
        """Send RTSP request to the server."""

        # Setup request
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()
            # Update RTSP sequence number.
            self.rtspSeq += 1

            # Write the RTSP request to be sent.
            request = 'SETUP ' + args[0] + ' RTSP/1.0\n' + \
            'CSeq: ' + str(self.rtspSeq) + '\n' + \
            'Transport: RTP/UDP; client_port= ' + str(self.rtpPort)
            print(request)
            # Keep track of the sent request.
            self.requestSent = self.SETUP

        elif requestCode == self.DESCRIBE and self.state == self.READY:
            # Update RTSP sequence number.
            self.rtspSeq += 1

            # Write the RTSP request to be sent.
            request = 'DESCRIBE ' + args[0] + ' RTSP/1.0\n' + \
                      'CSeq: ' + str(self.rtspSeq) + '\n' + \
                      'Session: ' + str(self.sessionId) + '\n' + \
                      'Accept: application/myformat'

            # Keep track of the sent request.
            self.requestSent = self.DESCRIBE

        # Play request
        elif requestCode == self.PLAY and self.state == self.READY:
            print(args)
            self.rtspSeq += 1
            range_info = ''

            if len(args) != 0:
                range_info = '\nRange: npt = '+str(args[0])+' -'
            request = 'PLAY ' + self.movie_name + ' RTSP/1.0\n' + \
                      'CSeq: ' + str(self.rtspSeq) + '\n' + \
                      'Session: ' + str(self.sessionId) + range_info

            self.requestSent = self.PLAY

        # Pause request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            self.rtspSeq += 1
            request = 'PAUSE ' + self.movie_name + ' RTSP/1.0\n' + \
                      'CSeq: ' + str(self.rtspSeq) + '\n' + \
                      'Session: ' + str(self.sessionId)

            self.requestSent = self.PAUSE

        # Teardown request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            self.rtspSeq += 1
            request = 'TEARDOWN ' + self.movie_name + ' RTSP/1.0\n' + \
                      'CSeq: ' + str(self.rtspSeq) + '\n' + \
                      'Session: ' + str(self.sessionId)

            self.requestSent = self.TEARDOWN
        else:
            return

        # Send the RTSP request using rtspSocket.
        self.rtspSocket.send(request.encode())

        print('\nData sent:\n' + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            try:
                reply = self.rtspSocket.recv(1024)

                if reply:
                    self.parseRtspReply(reply.decode("utf-8"))

                # Close the RTSP socket upon requesting Teardown
                if self.requestSent == self.TEARDOWN:
                    self.rtspSocket.shutdown(socket.SHUT_RDWR)
                    self.rtspSocket.close()
                    break
            except:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                self.rtpSocket.shutdown(socket.SHUT_RDWR)
                self.rtpSocket.close()
                self.teardownAcked = 1
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = str(data).split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # Process only if the server reply's sequence number is the same as the request's
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            # New RTSP session ID
            if self.sessionId == 0:
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:
                        # Update RTSP state.
                        self.state = self.READY
                        self.sendRtspRequest(self.DESCRIBE, self.movie_name)
                        # Open RTP port.
                        self.openRtpPort()
                    elif self.requestSent == self.DESCRIBE:
                        self.video_frame_count = int(lines[3].split('=')[-1])
                        self.video_fps = int(lines[4].split('=')[-1])
                        self.time_delay = round(1 / self.video_fps, 3)
                        self.modified_time_delay = self.time_delay
                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY
                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()
                    elif self.requestSent == self.TEARDOWN:
                        self.state = self.INIT
                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # Create a new datagram socket to receive RTP packets from the server
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set the timeout value of the socket to 0.5sec
        self.rtpSocket.settimeout(0.5)

        try:
            # Bind the socket to the address using the RTP port given by the client user
            self.rtpSocket.bind(("", self.rtpPort))
        except:
            tkMessageBox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else: # When the user presses cancel, resume playing.
            self.playMovie()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        rtp_port = sys.argv[1]
    else:
        rtp_port = 1234
    tk = Tk()
    Client(tk, '127.0.0.1', 10001, rtp_port, 'test.jpg')
    tk.mainloop()
