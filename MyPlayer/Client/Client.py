import sys
import time
import os
import socket
import threading
from audio_player import AudioPlayer
from RtpPacket import RtpPacket
import tkinter.messagebox as tkMessageBox

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
    SET_PARAMETER = 5

    # Initiation..
    def __init__(self, server_rtsp_port, server_plp_port, rtp_port, plp_port):

        # get addr and ports
        self.server_addr = '127.0.0.1'
        self.server_rtsp_port = int(server_rtsp_port)
        self.server_plp_port = int(server_plp_port)
        self.rtp_port = int(rtp_port)
        self.plp_port = int(plp_port)

        self.rtsp_seq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.rtsp_running = False

        # current video and audio parameters
        self.movie_name = ''
        self.packet_data = b''
        self.frameNbr = 0
        self.video_frame_no = 0
        self.video_frame_count = 0
        self.video_fps = 0
        self.audio_channels = 0
        self.audio_frame_rate = 0
        self.audio_sample_width = 0
        self.time_delay = 0
        self.modified_time_delay = 0

        # cache_settings
        self.cache_file = ''
        self.cache_extension = 'jpg'

    def retrievePlayList(self, type, keyword='', category=''):
        """
        :param keyword: keyword to search
        :param category: category to search
        :param keyword: category to search
        :return: a list of movie names
        """
        plp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        plp_socket.settimeout(1)
        plp_socket.bind(("", self.plp_port))
        addr = (self.server_addr, self.server_plp_port)
        try:
            if type == 'LIST':
                plp_socket.sendto('LIST'.encode('utf-8'), addr)
            elif type == 'CATEGORY':
                plp_socket.sendto('CATEGORY'.encode('utf-8'), addr)
            else:
                cmd = 'SEARCH ' + keyword + ' ' + category
                plp_socket.sendto(cmd.encode('utf-8'), addr)
            response, addr = plp_socket.recvfrom(8192)
            play_list = response.decode().split('\n')
        except:
            print("server not open")  # if server is not open, exit immediately
            sys.exit()
        plp_socket.close()
        return play_list

    def setupMovie(self, movie_name='test.mp4'):
        # loading resources
        if self.rtsp_running and self.state == self.INIT:
            tkMessageBox.showinfo("提示", "载入资源中无法切换，请稍候...")
            return

        # if can setup, insert into historylist
        self.historylist.insert(0, movie_name)
        if self.historylist.size() > 15:
            self.historylist.delete(15)

        # no session set up before, which means just opened client
        if not self.rtsp_running:
            self.rtsp_seq = 0
            self.movie_name = movie_name
            self.initNewMovie()
            self.connectToServer()
            self.subtitlebg['text'] = '正在载入资源...'
            self.sendRtspRequest(self.SETUP, movie_name)

        # change session while another one is open
        elif self.state != self.INIT:
            self.pauseMovie()
            time.sleep(0.5)
            self.play_end = True
            self.sendRtspRequest(self.TEARDOWN)
            self.play_record[self.movie_name] = self.video_frame_no
            self.rtpSocket.shutdown(socket.SHUT_RDWR)
            self.rtpSocket.close()

            # wait for the previous rtsp socket is closed
            while self.rtsp_running:
                pass
            self.state = self.INIT
            self.play_end = False
            print(movie_name)
            self.movie_name = movie_name
            self.rtsp_seq = 0
            self.initNewMovie()
            self.connectToServer()
            self.subtitlebg['text'] = '正在载入资源...'
            self.sendRtspRequest(self.SETUP, movie_name)

    # exit client
    def exitClient(self):
        # if there is a session going on
        if self.rtsp_running:
            self.play_end = True
            if self.state == self.INIT:
                self.rtspSocket.close()
            else:
                self.sendRtspRequest(self.TEARDOWN)
            self.play_record[self.movie_name] = self.cur_frame
            if not os.path.exists(os.path.dirname(self.record_file)):
                os.mkdir(os.path.dirname(self.record_file))
            with open(self.record_file, "w") as f:
                for i in range(self.historylist.size()):
                    f.write(self.historylist.get(i) + '\n')
                f.write(str(self.play_record[self.historylist.get(0)]))
            try:
                self.rtpSocket.shutdown(socket.SHUT_RDWR)
                self.rtpSocket.close()
            except:
                pass
            self.master.destroy()  # Close the gui window
        else:
            self.master.destroy()  # Close the gui window

    def pauseMovie(self):
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self, pos=-1):
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
        while True:
            try:
                # slightly less than the maximum
                data = self.rtpSocket.recv(50000)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    self.frameNbr = rtpPacket.seqNum()

                    # for video, combine the small packets together
                    if rtpPacket.payloadType() == 26:
                        if self.video_frame_no == rtpPacket.seqNum():
                            self.packet_data += rtpPacket.getPayload()
                        else:
                            self.video_frame_no = rtpPacket.seqNum()
                            self.collectVideoFrame(self.packet_data, self.video_frame_no-1)
                            self.packet_data = rtpPacket.getPayload()
                    # audio
                    elif rtpPacket.payloadType() == 10:
                        self.collectAudioFrame(rtpPacket.getPayload(), self.frameNbr)
                    # text
                    elif rtpPacket.payloadType() == 37:
                        self.collectSubtitle(rtpPacket.getPayload(), self.frameNbr)
                else:
                    # remaining data that belongs to video
                    if self.packet_data:
                        self.collectVideoFrame(self.packet_data, self.video_frame_no)
                    break

            except Exception as e:
                print("rtp", str(e))
                # Stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    break

                # Upon receiving ACK for TEARDOWN request,
                # close the RTP socket
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    self.rtsp_seq = 0
                    self.teardownAcked = 0
                    break

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.server_addr, self.server_rtsp_port))
        except Exception as e:
            print(str(e))

    def sendRtspRequest(self, requestCode, *args):
        # Setup request
        if requestCode == self.SETUP and self.state == self.INIT:
            self.rtsp_running = True
            threading.Thread(target=self.recvRtspReply).start()

            # Update RTSP sequence number.
            self.rtsp_seq += 1

            # Write the RTSP request to be sent.
            request = 'SETUP ' + args[0] + ' RTSP/1.0\n' + \
            'CSeq: ' + str(self.rtsp_seq) + '\n' + \
            'Transport: RTP/UDP; client_port= ' + str(self.rtp_port)
            print(request)
            # Keep track of the sent request.
            self.requestSent = self.SETUP

        elif requestCode == self.DESCRIBE and self.state == self.INIT:
            # Update RTSP sequence number.
            self.rtsp_seq += 1

            # Write the RTSP request to be sent.
            request = 'DESCRIBE ' + args[0] + ' RTSP/1.0\n' + \
                      'CSeq: ' + str(self.rtsp_seq) + '\n' + \
                      'Session: ' + str(self.sessionId) + '\n' + \
                      'Accept: application/myformat'

            # Keep track of the sent request.
            self.requestSent = self.DESCRIBE

        elif requestCode == self.SET_PARAMETER:
            self.rtsp_seq += 1

            # Write the RTSP request to be sent.
            request = 'SET_PARAMETER ' + args[0] + ' RTSP/1.0\n' + \
                      'CSeq: ' + str(self.rtsp_seq) + '\n' + \
                      'Session: ' + str(self.sessionId) + '\n' + \
                      args[0] + ': ' + args[1]

            # Do not keep track of the sent request, or it may interfere
            # self.requestSent = self.SET_PARAMETER

        # Play request
        elif requestCode == self.PLAY and self.state == self.READY:
            self.rtsp_seq += 1
            range_info = ''

            if len(args) != 0:
                range_info = '\nRange: npt = '+str(args[0])+' -'
            request = 'PLAY ' + self.movie_name + ' RTSP/1.0\n' + \
                      'CSeq: ' + str(self.rtsp_seq) + '\n' + \
                      'Session: ' + str(self.sessionId) + range_info

            self.requestSent = self.PLAY

        # Pause request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            self.rtsp_seq += 1
            request = 'PAUSE ' + self.movie_name + ' RTSP/1.0\n' + \
                      'CSeq: ' + str(self.rtsp_seq) + '\n' + \
                      'Session: ' + str(self.sessionId)

            self.requestSent = self.PAUSE

        # Teardown request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            self.rtsp_seq += 1
            request = 'TEARDOWN ' + self.movie_name + ' RTSP/1.0\n' + \
                      'CSeq: ' + str(self.rtsp_seq) + '\n' + \
                      'Session: ' + str(self.sessionId)

            self.requestSent = self.TEARDOWN
        else:
            return
        print('\nData sent:\n' + request)
        self.rtspSocket.send(request.encode())


    def recvRtspReply(self):
        while True:
            try:
                reply = self.rtspSocket.recv(1024)
                if reply:
                    self.parseRtspReply(reply.decode("utf-8"))
                else:
                    if self.requestSent == self.TEARDOWN:
                        self.rtspSocket.shutdown(socket.SHUT_RDWR)
                        self.rtspSocket.close()
                        break
                # Close the RTSP socket upon requesting Teardown
                if self.requestSent == self.TEARDOWN:
                    self.rtspSocket.shutdown(socket.SHUT_RDWR)
                    self.rtspSocket.close()
                    break
            except Exception as e:
                print(str(e))
                try:
                    self.rtspSocket.shutdown(socket.SHUT_RDWR)
                    self.rtspSocket.close()
                except:
                    pass
                break
        self.rtsp_running = False


    def parseRtspReply(self, data):
        lines = str(data).split('\n')
        seq_num = int(lines[1].split(' ')[1])

        # Process only if the server reply's sequence number is the same as the request's
        if seq_num == self.rtsp_seq:
            session = int(lines[2].split(' ')[1])

            # New RTSP session ID
            if self.sessionId == 0:
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:
                        # send DESCRIBE cmd next
                        self.sendRtspRequest(self.DESCRIBE, self.movie_name)
                        self.openRtpPort()

                    elif self.requestSent == self.DESCRIBE:
                        # parse the video information
                        self.video_frame_count = int(lines[3].split('=')[-1])
                        self.video_fps = int(lines[4].split('=')[-1])
                        self.audio_channels = int(lines[5].split('=')[-1])
                        self.audio_frame_rate = int(lines[6].split('=')[-1])
                        self.audio_sample_width = int(lines[7].split('=')[-1])
                        has_subtitle = int(lines[8].split('=')[-1])
                        if '默认' in self.subtitle_combobox['values']:
                            self.subtitle_combobox['values'] = ('无',)
                        if has_subtitle:
                            self.has_subtitle = True
                            self.subtitle_combobox['values'] += ('默认',)
                        self.time_delay = round(1 / self.video_fps, 3)
                        self.modified_time_delay = self.time_delay
                        self.audio_player = AudioPlayer(self.audio_channels, self.audio_frame_rate,
                                                        self.audio_sample_width)
                        self.state = self.READY
                        self.slider['state'] = 'normal'
                        if self.memory != '':
                            self.setSliderPosition(self.memory)
                        self.subtitlebg['text'] = '资源加载完成。'

                    elif self.requestSent == self.SET_PARAMETER:
                        pass

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

    # Open RTP socket binded to a specified port.
    def openRtpPort(self):
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.rtpSocket.bind(("", self.rtp_port))
        except Exception as e:
            print(str(e))
