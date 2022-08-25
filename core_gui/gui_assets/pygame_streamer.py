# Pygame --> Numpy --> FFMPEG pipeline --> HLS
# tested on Ubuntu20.04, python 3.8.10
# 20220802
# Kentamt

import sys
import time
from queue import Queue, Empty
from threading import Thread

from multiprocessing import Process, Queue
import subprocess as sp
import numpy as np
import pygame


ON_POSIX = 'posix' in sys.builtin_module_names


def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

class PygameStreamer():
    def __init__(self, w, h, fps,
                 bitrate='10000k',
                 speed_option='ultrafast',
                 format='hls',
                 chunk_time=1,
                 sdp_name='pygame_streamer.sdp',
                 output='./hls/live.m3u8',
                 verbose=False
                 ):
        
        self._verbose = verbose
        
        self._w = w
        self._h = h
        self._bitrate = bitrate
        self._speed_option = speed_option
        self._fps = str(fps)
        self._format = format
        self._output = None
        self._output = output
        
        # speed parameter
        self._k = 0.2
        self._margin = 0.005
        
        # For hls options
        self._chunk_time = str(chunk_time)
        
        # For dash options
        self._remove_at_exit = str(1)
        
        # For rtp options
        self._sdp_name = sdp_name
        
        # subprocess for ffmpeg
        self._sleep_sec = 1.0 / float(self._fps)
        self._previous_data = None        
        self._writing_process = None
       
        # subprocess for writing 
        self.image_queue = Queue()
        self.stop_request = Queue()
        self._running = True
        self._finished = False
        self._async_write_proc = Process(target=self.async_write, args=(self.image_queue, self.stop_request))
        self._async_write_proc.start()

    def terminate(self):
        self.stop_request.put(True)
        if self._finished:
            if self._verbose:
                print('terminate subprocesses')
                
            self._writing_process.stdin.close()
            self._writing_process.kill()
            self._async_write_proc.terminate()
  
    def pygame_to_image(self, screen):
        array_data: np.array = pygame.surfarray.array3d(screen)
        array_data = array_data.astype(np.uint8)
        array_data = array_data.swapaxes(0, 1)
        array_data = array_data[..., [2, 1, 0]].copy()  # RGB2BGR
        return array_data
    
    def __get_speed(self, line):
        ratio = None
        words = line.split(' ')
        
        for word in words:
            elems = word.split('=')
            if elems[0] == 'speed' and elems[1]  == 'N/A':
                pass
            elif elems[0] == 'speed' and elems[1] != '':
                ratio = float(elems[1].split('x')[0])
        return ratio
    
    def __adjust_speed(self):
        """
        if the output of ffmpeg contains speed infomation,
        adjust sleep time with the speed.
        """
        try:
            line = self._q.get_nowait()
        except Empty:
            # if there is no massage from ffmpeg, do nothing.
            pass 
        else:
            line = line.decode("utf-8")
            ratio = self.__get_speed(line)
            
            if ratio is not None:
                
                if self._verbose:
                    print(ratio,  flush=True)
                    
                if ratio < 1.0 + self._margin:
                    self._sleep_sec *= 1.0 - (1.0 - ratio) * self._k
                elif 1.0 - self._margin < ratio:
                    self._sleep_sec *= 1.0 + (ratio - 1.0) * self._k
                    
                    
    def __set_previous_data(self, array_data):
        self._previous_data = array_data # TODO: check if deepcopy is needed
        
        
    def __remove_data(self):
        while not self.image_queue.empty():
            self.image_queue.get()
            
            
    def async_write(self, image_queue: Queue, stop_request :Queue):
        
        self.__init_process()
        
        while self._running:
            
            if not stop_request.empty():
                self._running = False
            
            if not image_queue.empty():
                array_data = image_queue.get()
                
                self._writing_process.stdin.write(array_data.tobytes())
                self.__adjust_speed()
                self.__set_previous_data(array_data)
                self.__remove_data()
                    
            else:
                if self._previous_data is not None:
                    self._writing_process.stdin.write(self._previous_data.tobytes())
                    self.__adjust_speed()
                    
            time.sleep(self._sleep_sec)
            

        self._finished = True
        
    def __init_process(self):
        if self._format == 'hls':
            command = ['ffmpeg',
                       # ----------- input --------------------
                       '-y',
                       '-f', 'rawvideo',
                       '-vcodec', 'rawvideo',
                       '-pix_fmt', 'bgr24',
                       '-s', f'{self._w}x{self._h}',
                       '-r', self._fps,
                       '-i', '-',  # input from stdin
                       # ----------- output --------------------
                       '-c:v', 'libx264',
                       '-pix_fmt', "yuv420p",
                       '-preset', self._speed_option,
                       '-b:v', self._bitrate,
                       '-hls_time', self._chunk_time,
                       '-hls_flags', "delete_segments",
                       '-force_key_frames', "expr:gte(t,n_forced*1)",
                       '-f', self._format,
                       self._output]

        elif self._format == 'dash':
            # self._output = '/dev/shm/dash/live.mpd'
            command = ['ffmpeg',
                       # ----------- input --------------------
                       '-y',
                       '-f', 'rawvideo',
                       '-vcodec', 'rawvideo',
                       '-pix_fmt', 'bgr24',
                       '-s', f'{self._w}x{self._h}',
                       '-r', self._fps,
                       '-i', '-',  # input from stdin
                       # ----------- output --------------------
                       '-c:v', 'libx264',
                       '-pix_fmt', "yuv420p",
                       '-preset', self._speed_option,
                       '-b:v', self._bitrate,
                       '-force_key_frames', "expr:gte(t,n_forced*1)",
                       '-seg_duration', self._chunk_time,
                       '-use_timeline', '1',
                       '-use_template', '1',
                       '-remove_at_exit', self._remove_at_exit,
                       '-f', self._format,
                       self._output]

        elif self._format == 'rtp':
            # self._output = f'rtp://239.0.0.1:50004' # multicast
            command = ['ffmpeg',
                       # ----------- input --------------------
                       '-y',
                       '-f', 'rawvideo',
                       '-vcodec', 'rawvideo',
                       '-pix_fmt', 'bgr24',
                       '-s', f'{self._w}x{self._h}',
                       '-r', self._fps,
                       '-i', '-',  # input from stdin
                       # ----------- output --------------------
                       '-c:v', 'libx264',
                       '-pix_fmt', "yuv420p",
                       '-preset', self._speed_option,
                       '-b:v', self._bitrate,
                       '-sdp_file', self._sdp_name,
                       '-f', self._format,
                       self._output]
        else:
            raise Exception("Sorry, unknown format. Use hls, dash or rtp.")
        
        self._writing_process = sp.Popen(command,
                                         stdin=sp.PIPE,
                                         stderr=sp.STDOUT,
                                         stdout=sp.PIPE,
                                         close_fds=ON_POSIX)
        
        # Use a thread to parse ffmpeg output without blocking
        self._q = Queue()
        t = Thread(target=enqueue_output,
                   args=(self._writing_process.stdout, self._q))
        t.daemon = True # thread dies at the end of the program
        t.start()
        
