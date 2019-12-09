class Subtitle:
    def __init__(self, frame_count, fps):
        self.no2subtitle = {}
        self.frame_count = frame_count
        self.fps = fps
        self.fph = fps * 3600
        self.fpm = fps * 60
        self.frame2subtitle = {}
        self.frame_no = 0

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
        self.no2subtitle[subtitle_no] = subtitle
        self.parseTime(time, subtitle_no)


    def parseTime(self, line, subtitle_no):
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
        for i in range(start_frame, end_frame):
            self.frame2subtitle[i] = subtitle_no

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
