## TASK-2 服务端运行环境与说明描述



**运行环境**

语言：Python3.7 

操作系统：Windows10

依赖库：cv2，PyAudio，pydub，simpleaudio（服务端和客户端）

PyAudio可以从https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio下载相应的.whl文件，然后pip install之。

pydub安装参考https://github.com/jiaaro/pydub#installation。



**说明描述**

运行服务端的命令为在该目录下命令行运行：

```
python Server.py
```

其中可以有三个参数，分别为服务端RTSP端口，RTP端口和用于传输播放列表等信息的端口。默认的都是大端口，故应该不需要指定端口。

此后不用进行任何操作。



提供了三个测试用的视频（一个视频是mov格式，其他是mp4格式，mov格式视频由于音频解析库的问题声音有问题，但不会报错；mp4格式声音没有问题，音频的效果请参考mp4视频的）和一份字幕。添加自定义测试文件详见Client的说明文件。

