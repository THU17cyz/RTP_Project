import socket
from RtpPacket import RtpPacket
import time
import threading
from video_extractor import VideoCapturer
from audio_player import AudioCapturer
import ctypes
from subtitle import Subtitle

# set time.sleep() accuracy
winmm = ctypes.WinDLL('winmm')
winmm.timeBeginPeriod(1)


class Server:
    def __init__(self, rtsp_port, rtp_port, plp_port, src_folder):
        self.rtsp_port = int(rtsp_port)
        self.rtp_port = int(rtp_port)
        self.plp_port = int(plp_port)
        self.src_folder = src_folder
        self.rtp_socket = None
        self.plp_socket = None
        self.rtsp_socket = None
        self.packet_size = 48000
        self.clients = [None] * 100  # stores the client info

        self.openRtp()  # open rtp port
        threading.Thread(target=self.openPlp).start()  # start plp listening
        threading.Thread(target=self.openRtsp).start()  # start listening for rtsp connections

        self.vacancy = list(range(99, 0, -1))
        self.sessionPool = list(range(99, 0, -1))  # distributes session id


        self.play_list = ['test.mp4', 'hires.mp4', 'test1.mp4']  # all movies stored at the server
        self.play2category = {'test.mp4': 'test1', 'hires.mp4': 'test2', 'test1.mp4': 'test2'}
        self.category_list = ['test1', 'test2']
        self.has_subtitle =  {'test.mp4': 'test.srt', 'hires.mp4': None, 'test1.mp4': 'test.srt'}

    # open rtp port
    def openRtp(self):
        self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the timeout value of the socket to 0.5sec
        self.rtp_socket.settimeout(0.5)
        try:
            # Bind the socket to the address using the RTP port given by the server user
            self.rtp_socket.bind(("", self.rtp_port))
        except Exception as e:
            print(str(e))

    def openPlp(self):
        self.plp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.plp_socket.bind(("", self.plp_port))
        except Exception as e:
            print(str(e))
        while True:
            try:
                query, addr = self.plp_socket.recvfrom(8192)
                data = query.decode()
                # list all movies
                if data == 'LIST':
                    response = '\n'.join(self.play_list)
                    self.plp_socket.sendto(response.encode('utf-8'), addr)

                # list all categories
                elif data == 'CATEGORY':
                    response = '\n'.join(self.category_list)
                    self.plp_socket.sendto(response.encode('utf-8'), addr)

                # list all movies with the cmd substring
                elif data.split(' ')[0] == 'SEARCH':
                    print(data)
                    keyword = data.split(' ')[1]
                    category = data.split(' ')[2]
                    all_category = False
                    if category == '所有':
                        all_category = True
                    res = []
                    for movie in self.play_list:
                        if keyword in movie.split('.')[0] and (all_category or self.play2category[movie] == category):
                            res.append(movie)
                    response = '\n'.join(res)
                    self.plp_socket.sendto(response.encode('utf-8'), addr)
            except Exception as e:
                print('plp', str(e))
                break

    # open rtsp port and start listening
    def openRtsp(self):
        self.rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Bind the socket to the address using the RTP port given by the server user
            self.rtsp_socket.bind(("", self.rtsp_port))
        except Exception as e:
            print(str(e))

        # start listening for connections
        self.rtsp_socket.listen(100)
        while True:
            client, addr = self.rtsp_socket.accept()

            # initialize client info
            client_info = {'socket': client,
                           'addr': addr[0],
                           'seq': 1,
                           'sending': False,
                           'buffer_full': False,
                           'frame_num': 0}
            i = self.vacancy.pop()
            self.clients[i] = client_info

            print("openrtsp", client, i)

            # start listening for rstp requests
            threading.Thread(target=self.recvRtsp, args=(client, i)).start()

    # receive rtsp requests
    def recvRtsp(self, socket, i):
        while True:
            try:
                request = socket.recv(8192)
                if request:
                    print("pairleft")
                    self.parseRtspRequest(request.decode("utf-8"), i)
                    print("pairright")
                else:
                    print("empty")
                    break
            except Exception as e:
                print('rtsp', str(e))
                break
        try:
            self.clients[i]['video_extractor'].releaseVideo()
        except:
            pass
        self.clients[i]['video_extractor'] = None

    def setupMediaExtractor(self, i):
        movie_name = self.clients[i]['movie_name']
        self.clients[i]['video_extractor'] = VideoCapturer(movie_name)
        video_extractor = self.clients[i]['video_extractor']
        fps = video_extractor.fps
        frame_count = video_extractor.frame_count
        self.clients[i]['audio_extractor'] = AudioCapturer(movie_name, fps, frame_count)
        if self.clients[i]['subtitle_file'] is not None:
            print("srt")
            self.clients[i]['subtitle'] = Subtitle(frame_count, fps, self.clients[i]['subtitle_file'])
            # subtitle_extractor = SubtitleExtractor(self.clients[i]['subtitle_file'])
            # self.clients[i]['subtitle_extractor'] = subtitle_extractor
            # subtitle = Subtitle(frame_count, fps)
            # while True:
            #     data, subtitle_no = subtitle_extractor.extractLine()


    def sendRtp(self, i):
        while True:
            if self.clients[i]['sending'] and not self.clients[i]['buffer_full']:
                try:

                    # frame_num = self.clients[i]['frame_num']
                    #
                    # src_name = self.src_folder + '/%d.jpg' % frame_num
                    # file = open(src_name, "rb")
                    # data = file.read()
                    # file.close()
                    start_pos = self.clients[i]['start_pos']
                    # print(start_pos)
                    if start_pos is not None:
                        data, frame_no = self.clients[i]['video_extractor'].captureFrame(start_pos)
                        audio_data, audio_frame_no = self.clients[i]['audio_extractor'].captureFrame(start_pos)
                        self.clients[i]['start_pos'] = None
                        if self.clients[i]['subtitle_file'] is not None:
                            # subtitle_data, subtitle_no = self.clients[i]['subtitle_extractor'].extractLine()
                            # print(subtitle_data)
                            if frame_no in self.clients[i]['subtitle'].frame2subtitle.keys():
                                subtitle = self.clients[i]['subtitle'].frame2subtitle[frame_no]
                            else:
                                subtitle = None
                    else:
                        data, frame_no = self.clients[i]['video_extractor'].captureFrame()
                        audio_data, audio_frame_no = self.clients[i]['audio_extractor'].captureFrame()
                        if self.clients[i]['subtitle_file'] is not None:
                            # subtitle_data, subtitle_no = self.clients[i]['subtitle_extractor'].extractLine()
                            # print(subtitle_data)
                            if frame_no in self.clients[i]['subtitle'].frame2subtitle.keys():
                                subtitle = self.clients[i]['subtitle'].frame2subtitle[frame_no]
                            else:
                                subtitle = None


                    if frame_no != -1 and audio_frame_no != -1:
                        # print(audio_frame_no, len(audio_data))
                        rtpPacket = RtpPacket()
                        length = len(data)
                        #print(length)
                        start = 0
                        while start + self.packet_size < length:
                            this_data = data[start:start+self.packet_size]
                            rtpPacket.encode(2, 0, 0, 0, frame_no, 0, 26, 0, this_data)
                            #print("leng", len(this_data))
                            self.sendPacket(rtpPacket, i)
                            time.sleep(0.01)  # wait for 0.01 second
                            start += self.packet_size
                        this_data = data[start:length]
                        rtpPacket.encode(2, 0, 0, 0, frame_no, 0, 26, 0, this_data)
                        #print("leng", len(this_data))
                        self.sendPacket(rtpPacket, i)
                        if frame_no == self.clients[i]['video_extractor'].frame_count - 1:
                            rtpPacket = RtpPacket()
                            rtpPacket.encode(2, 0, 0, 0, frame_no+1, 0, 26, 0, b'')
                            self.sendPacket(rtpPacket, i)


                        time.sleep(0.01)  # wait for 0.01 second
                        audio_packet = RtpPacket()

                        audio_packet.encode(2, 0, 0, 0, audio_frame_no, 0, 10, 0, audio_data)

                        self.sendPacket(audio_packet, i)
                        time.sleep(0.01)  # wait for 0.01 second

                        rtpPacket = RtpPacket()
                        rtpPacket.encode(2, 0, 0, 0, frame_no, 0, 26, 0, data)

                        if self.clients[i]['subtitle_file'] is not None:
                            if subtitle is not None:
                                subtitle_packet = RtpPacket()
                                subtitle_packet.encode(2, 0, 0, 0, frame_no, 0, 37, 0, subtitle.encode())
                                self.sendPacket(subtitle_packet, i)

                        self.clients[i]['frame_num'] = frame_no + 1
                        #print(frame_no)
                except Exception as e:
                    print(str(e))
                    break
            elif self.clients[i]['video_extractor'] is None:
                break
        print("got out of rtp thread")

    # send an rtp packet
    def sendPacket(self, data, i):
        addr = self.clients[i]['addr']
        port = self.clients[i]['rtp_port']
        self.rtp_socket.sendto(data.getPacket(), (addr, port))

    # parses rtsp requests and reply them
    def parseRtspRequest(self, data, i):
        lines = str(data).split('\n')
        cmd = lines[0].split(' ')[0]
        rtsp_seq = int(lines[1].split(' ')[1])
        print(rtsp_seq, self.clients[i]['seq'])
        if rtsp_seq == self.clients[i]['seq']:
            self.clients[i]['seq'] += 1

            if cmd == 'SETUP':
                self.clients[i]['movie_name'] = src_folder + lines[0].split(' ')[1]
                self.clients[i]['subtitle_file'] = self.has_subtitle[self.clients[i]['movie_name']]
                rtpDestPort = int(lines[2].split(' ')[-1])
                self.clients[i]['rtp_port'] = rtpDestPort
                session = self.sessionPool.pop()
                self.clients[i]['session'] = session
                reply = 'RTSP/1.0 200 OK\nCSeq: ' + str(rtsp_seq) + '\nSession: ' + str(session)
                self.setupMediaExtractor(i)
                threading.Thread(target=self.sendRtp, args=(i,)).start()

            elif cmd == 'DESCRIBE':
                session = int(lines[2].split(' ')[-1])
                if session == self.clients[i]['session']:
                    video_capturer = self.clients[i]['video_extractor']
                    audio_capturer = self.clients[i]['audio_extractor']
                    video_frame_count = str(video_capturer.frame_count)
                    video_frame_count = 'video_frame_count=' + video_frame_count + '\n'
                    video_fps = str(video_capturer.fps)
                    video_fps = 'video_fps=' + video_fps + '\n'
                    audio_channels = str(audio_capturer.channels)
                    audio_channels = 'audio_channels=' + audio_channels + '\n'
                    audio_frame_rate = str(audio_capturer.frame_rate)
                    audio_frame_rate = 'audio_frame_rate=' + audio_frame_rate + '\n'
                    audio_sample_width = str(audio_capturer.sample_width)
                    audio_sample_width = 'audio_sample_width=' + audio_sample_width + '\n'
                    if self.clients[i]['subtitle_file'] is not None:
                        has_subtitle = '1'
                    else:
                        has_subtitle = '0'
                    has_subtitle = 'has_subtitle=' + has_subtitle
                    reply = 'RTSP/1.0 200 OK\n' + \
                            'CSeq: ' + str(rtsp_seq) + '\n' + \
                            'Session: ' + str(session) + '\n'
                    reply += video_frame_count
                    reply += video_fps
                    reply += audio_channels
                    reply += audio_frame_rate
                    reply += audio_sample_width
                    reply += has_subtitle

            elif cmd == 'SET_PARAMETER':
                session = int(lines[2].split(' ')[-1])
                if session == self.clients[i]['session']:
                    line = lines[3].split(': ')
                    param, val = line[0], line[1]
                    if param == 'buffer_full':
                        if val == 'true':
                            self.clients[i]['buffer_full'] = True
                        else:
                            self.clients[i]['buffer_full'] = False
                    elif param == 'compress':
                        try:
                            if val == '1':
                                self.clients[i]['video_extractor'].resize_rate = 1
                            elif val == '2':
                                self.clients[i]['video_extractor'].resize_rate = 0.7
                            else:
                                self.clients[i]['video_extractor'].resize_rate = 0.5
                        except:
                            pass
                return

            elif cmd == 'PLAY':
                session = int(lines[2].split(' ')[-1])
                if len(lines) > 3:
                    range = lines[3].split('= ')[-1]
                    print(range)
                    start_pos = int(range.split('-')[0].strip())
                    print(start_pos)
                    end_pos = range.split('-')[1].strip()
                    if len(end_pos) == 0:
                        end_pos = -1
                    else:
                        end_pos = int(end_pos)
                    print(start_pos)
                else:
                    start_pos = None
                try:
                    if session == self.clients[i]['session']:
                        self.clients[i]['sending'] = True
                        self.clients[i]['start_pos'] = start_pos
                        reply = 'RTSP/1.0 200 OK\nCSeq: ' + str(rtsp_seq) + '\nSession: ' + str(session)
                    else:
                        reply = 'RTSP/1.0 454 Session not found\nCSeq: ' + str(rtsp_seq) + '\nSession: ' + str(session)
                except Exception as e:
                    print(str(e))

            elif cmd == 'PAUSE':
                session = int(lines[2].split(' ')[-1])
                if session == self.clients[i]['session']:
                    self.clients[i]['sending'] = False
                    reply = 'RTSP/1.0 200 OK\nCSeq: ' + str(rtsp_seq) + '\nSession: ' + str(session)
                else:
                    reply = 'RTSP/1.0 454 Session not found\nCSeq: ' + str(rtsp_seq) + '\nSession: ' + str(session)

            elif cmd == 'TEARDOWN':
                session = int(lines[2].split(' ')[-1])
                if session == self.clients[i]['session']:
                    self.clients[i]['sending'] = False
                    reply = 'RTSP/1.0 200 OK\nCSeq: ' + str(rtsp_seq) + '\nSession: ' + str(session)
                else:
                    reply = 'RTSP/1.0 454 Session not found\nCSeq: ' + str(rtsp_seq) + '\nSession: ' + str(session)
                self.clients[i]['socket'].send(reply.encode())
                # self.clients[i]['socket'].shutdown(socket.SHUT_RDWR)
                # self.clients[i]['socket'].close()
                self.clients[i]['video_extractor'].releaseVideo()
                self.clients[i]['video_extractor'] = None

                self.sessionPool.append(self.clients[i]['session'])
                self.vacancy.append(i)
                # self.clients = self.clients[:i] + self.clients[i+1:]
                return
            else:
                return
            print(reply)
            self.clients[i]['socket'].send(reply.encode())


if __name__ == "__main__":
    rtsp_port = 10001
    rtp_port = 22222
    plp_port = 22233
    src_folder = ''
    server = Server(rtsp_port, rtp_port, plp_port, src_folder)
