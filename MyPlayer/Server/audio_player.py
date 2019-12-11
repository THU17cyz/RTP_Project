from pydub import AudioSegment
import pyaudio


class AudioPlayer:
    def __init__(self, channels, frame_rate, sample_width):
        self.audio = pyaudio.PyAudio()
        self.rate = 1
        self.channels = channels
        self.frame_rate = frame_rate
        self.sample_width = sample_width
        self.stream = self.audio.open(format=self.audio.get_format_from_width(self.sample_width),
                                      channels=self.channels,
                                      rate=self.frame_rate,
                                      output=True)

    def playAudio(self, data, rate=1):
        """
        play a segment of raw audio
        :param data: raw audio data
        :param rate: speed (not frame_rate)
        :return: None
        """
        if rate != 1:
            data = change_speed(data, self.sample_width, self.frame_rate, self.channels, rate)
        self.stream.write(data)


def change_speed(data, sample_width, frame_rate, channels, speed=1.0):
    sound = AudioSegment(
        # raw audio data (bytes)
        data=data,

        # 2 byte (16 bit) samples
        sample_width=sample_width,

        # 44.1 kHz frame rate
        frame_rate=frame_rate,

        # stereo
        channels=channels
    )
    sound = speed_change(sound, speed)
    return sound.raw_data


def speed_change(sound, speed=1.0):
    # Manually override the frame_rate. This tells the computer how many
    # samples to play per second
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })
    # convert the sound with altered frame rate to a standard frame rate
    # so that regular playback programs will work right. They often only
    # know how to play audio at standard frame rate (like 44.1k)
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)


class AudioCapturer:
    def __init__(self, audio, video_fps, frame_count):
        extension = audio.split('.')[-1]
        self.audio = AudioSegment.from_file(audio, format=extension)
        self.duration = int(1000 * self.audio.duration_seconds)  # time should be smaller than this value
        self.sample_width = self.audio.sample_width
        self.frame_rate = self.audio.frame_rate
        self.channels = self.audio.channels
        self.interval = int(1000 / video_fps)
        self.frame_count = frame_count  # get this from video
        self.frame_no = 0
        print(self.sample_width, self.frame_rate, self.channels)

    def captureFrame(self, pos=-1):
        if pos != -1:
            if pos >= self.frame_count:
                return '', -1
            self.frame_no = pos
        if self.frame_no >= self.frame_count:
            return '', -1

        start = int(self.frame_no * self.duration / self.frame_count)
        end = min(start + self.interval, self.duration - 1)
        data = self.audio[start:end].raw_data
        self.frame_no += 1
        return data, self.frame_no - 1

