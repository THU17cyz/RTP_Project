class Subtitle:
    def __init__(self, frame_count, fps, subtitle_file):
        self.support_subtitle_ext = ['srt']
        assert subtitle_file.split('.')[-1] in self.support_subtitle_ext
        f = open(subtitle_file)
        self.subtitle = f.read().split('\n')
        f.close()
        self.line_no = 0
        self.subtitle_no = 0

        self.frame2subtitle = []
        self.no2subtitle = {}
        self.frame_count = frame_count
        self.fps = fps
        self.fph = fps * 3600
        self.fpm = fps * 60
        self.frame2subtitle = {}
        self.frame_no = 0

        while True:
            data, subtitle_no = self.extractLine()
            if subtitle_no == -1:
                break
            self.generateFrame2Subtitle(data, subtitle_no)
        print(self.frame2subtitle)

    def extractLine(self):
        try:
            while self.subtitle[self.line_no].strip() != str(self.subtitle_no+1):
                self.line_no += 1
        except IndexError:
            return '', -1
        self.line_no += 1
        data = ''
        while self.subtitle[self.line_no].strip() != '':
            data += self.subtitle[self.line_no] + '\n'
            self.line_no += 1
        self.subtitle_no += 1
        return data, self.subtitle_no-1

    def generateFrame2Subtitle(self, subtitle, subtitle_no):
        """
        get subtitle and its number and store them
        :param subtitle: subtitle content
        :param subtitle_no: subtitle number
        :return: None
        """
        lines = subtitle.split('\n', 1)
        time = lines[0]
        subtitle = lines[1]
        # self.no2subtitle[subtitle_no] = subtitle
        self.parseTime(time, subtitle_no, subtitle)


    def parseTime(self, line, subtitle_no, subtitle):
        """
        parse .srt time and store info into frame2subtitle
        :param line: start time --> end time
        :param subtitle_no: subtitle number
        :return: None
        """
        start_and_end = line.split('-->')
        start = start_and_end[0].strip()
        end = start_and_end[1].strip()
        start_frame = self.calculateFrame(start)
        end_frame = self.calculateFrame(end)
        # for i in range(start_frame, end_frame):
        #     self.frame2subtitle[i] = subtitle_no
        self.frame2subtitle[start_frame] = str(end_frame-start_frame) + '\n' + subtitle

    def calculateFrame(self, format_time):
        """
        time --> frame
        :param format_time: time
        :return: frame
        """
        time = format_time.split(':')
        frame = 0
        frame += int(time[0]) * self.fph
        frame += int(time[1]) * self.fpm
        sec = time[2].split(',')
        frame += int(sec[0]) * self.fps
        frame += int(sec[1]) * self.fps // 1000
        return frame
