"""
  detector.py: Original work Copyright (C) 2021 by Blewett

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
import pyaudio
import wave
import os
import sys
import time
import signal
import threading
from threading import Thread
from array import array
from math import sqrt

DEFAULT_RECORDING_THRESOLD = 1280
DEFAULT_RECORD_SECONDS = 2

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
# 16 bits == 2 bytes
WIDTH = 2

RECORD_WAVE_OUTPUT_FILENAME = ""
PLAY_WAVE_OUTPUT_FILENAME = ""

global audio
global audio_index
global record
global record_filename
global recording_seconds
global recording_thresold
global play
global play_arg
global play_files
global play_list
global play_index
global echo
global allow_echo_reverb

class wave_buffer:
    def __init__(self):
        self.filename = ""
        self.data = 0
        self.buffer_count = 0
        self.sample_width = 0
        self.channels = 0
        self.framerate = 0

    def load_file(self, filename):
        wf = wave.open(filename, 'rb')

        wave_data = []
        data = 1        
        while data:
            data = wf.readframes(CHUNK)
            wave_data.append(data)

        self.filename = filename
        self.data = wave_data
        self.buffer_count = len(wave_data)
        self.sample_width = wf.getsampwidth()
        self.channels = wf.getnchannels()
        self.framerate = wf.getframerate()

        wf.close()

    def load_data(self, filename, data):
        self.filename = filename
        self.data = data
        self.buffer_count = len(data)
        self.sample_width = WIDTH
        self.channels = CHANNELS
        self.framerate = RATE
#

def initialize():
    global audio
    global audio_index

    audio = pyaudio.PyAudio()

    print("----------------------recording device list---------------------")
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            print("Input Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))

    print(" enter q to quit")
    print("-------------------------------------------------------------")

    loop = True
    while loop:
        letter = input("Which input do you want to use: ")
        if letter == 'q':
            exit(0)
        if letter.isalpha() == True or letter.isdigit() == False:
            print("Choose a number from the list of input devices")
            exit(0)
        loop = False

    audio_index = int(letter)
    print("recording via index " + str(audio_index))
    print_options("record starting")
#

def record_wave(wave_file):
    global audio
    global audio_index
    global recording_seconds
    global play
    global play_list

    letter = input("Press enter to begin recording: ")
    if letter == 'q':
        audio.terminate()
        exit(0)

    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=audio_index,
                        frames_per_buffer=CHUNK)

    record_loop = True
    while record_loop:

        stream.start_stream()
        print("* recording")

        wave_data = []
        for i in range(0, int(RATE / CHUNK * recording_seconds)):
            data = stream.read(CHUNK)
            wave_data.append(data)

        stream.stop_stream()
        print("* recording ended")

        print("* replaying")
        wb = wave_buffer()
        wb.load_data(wave_file, wave_data)
        play_wave(wb)
        print("* replaying ended")

        letter = input("Record again enter y: ")
        if letter == 'q':
            audio.terminate()
            exit(0)
        if letter != 'y':
            record_loop = False

    stream.close()

    wf = wave.open(wave_file, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(wave_data))
    wf.close()

    return wb
#

def gather_wave(stream, data):
    global recording_seconds

    print("* gathering")

    wave_data = []
    wave_data.append(data)

    for i in range(1, int(RATE / CHUNK * recording_seconds)):
        data = stream.read(CHUNK)
        wave_data.append(data)

    print("* gathering ended")
    wb = wave_buffer()
    wb.load_data("echo", wave_data)

    return wb
#

def play_wave(wave_buffer):
    global audio

    print("wave file: " + str(wave_buffer.filename))

    stream = audio.open(format=audio.get_format_from_width(wave_buffer.sample_width),
                        channels=wave_buffer.channels,
                        rate=wave_buffer.framerate,
                        output=True)

    print("* Wave start *")

    stream.start_stream()

    i = 0
    while i < wave_buffer.buffer_count:
        stream.write(wave_buffer.data[i])
        i = i + 1

    # stream.stop_stream()
    stream.close()

    print("* Wave complete *")
#


def rmsa_calc(num):
#     Calculate Root Mean Square of an array
    return sqrt(sum(n*n for n in num)/len(num))

def listen():
    global audio
    global recording_seconds
    global allow_echo_reverb
    global play
    global play_list
    global play_index

    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    #
    # start of while loop
    #
    play_index = 0
    while True:
        data = stream.read(CHUNK)
        x = rmsa_calc(array('h', data))
        if (x >= recording_thresold):
            print(("* We heard a noise " + str(int(x)) + " *"))
            if echo and play_index >= len(play_list):
                play_index = 0
                wb = gather_wave(stream, data)
                if allow_echo_reverb == False:
                    stream.stop_stream()
                play_wave(wb)
                if allow_echo_reverb == False:
                    stream.start_stream()
            elif play:
                if len(play_list) > 0:
                    if play_index >= len(play_list):
                        play_index = 0
                    if allow_echo_reverb == False:
                        stream.stop_stream()
                    play_wave(play_list[play_index])
                    play_index += 1
                    if allow_echo_reverb == False:
                        stream.start_stream()
# end listen

def user_exit():
    while True:
        print("Enter q to exit: ")
        sys.stdout.flush()

        ch = sys.stdin.read(1)
        if ch == 'q':
            os.kill(os.getpid(), signal.SIGTERM)
#

def check_writable(prog, file):
    try:
        f = open(file, "a")
    except IOError:
        print(prog + ": could not open for writing \"" + file + "\"")
        return False

    f.close()
    return True
#

def check_readable(prog, file):
    try:
        f = open(file, "r")
    except IOError:
        print(prog + ": could not read \"" + file + "\"")
        return False

    f.close()
    return True
#

def parse_args():

    global record
    record = False
    global record_filename
    record_filename = RECORD_WAVE_OUTPUT_FILENAME

    global play
    play = False
    global play_arg
    global play_files

    global echo
    echo = False

    global allow_echo_reverb
    allow_echo_reverb = False

    global recording_seconds
    recording_seconds = DEFAULT_RECORD_SECONDS

    global recording_thresold
    recording_thresold = DEFAULT_RECORDING_THRESOLD

    argc = len(sys.argv)
    prog = sys.argv[0]
    i = 1
    while i < argc:
        arg = sys.argv[i]

        # record a wav
        if (arg == "-record"):
            i += 1
            if i >= argc:
                print(prog + ": Missing filename needed for -record")
                exit(1)

            record_filename = sys.argv[i]
            record = True
            i += 1
            if check_writable(prog, record_filename) == False:
                print(prog + " -record " + record_filename + " is not writable.")
                exit(1)

            continue
    
        # echo
        if (arg == "-echo"):
            i += 1
            echo = True
            continue

        # allow_echo_reverb
        if (arg == "-allow_echo_reverb"):
            i += 1
            allow_echo_reverb = True
            continue

        # play a wav
        if (arg == "-play"):
            i += 1
            if i >= argc:
                print(prog + ": Missing filename needed for -play")
                exit(1)

            play_arg = sys.argv[i]
            i += 1

            for f in play_arg.split():
                if check_readable(prog, f) == False:
                    print(prog + " -play " + f + " is not readable.")
                    exit(1)
                play_files.append(f)

            play = True
            continue
    
        # recording_seconds
        if (arg == "-recording_seconds"):
            i += 1
            if i >= argc:
                print(prog + ": Missing number of seconds for -recording_seconds")
                exit(1)

            recording_seconds = sys.argv[i]
            i += 1
            if recording_seconds.isdigit() == False:
                print(prog + ": the -recording_seocnds must be a number")
                exit(1)

            recording_seconds = int(recording_seconds)
            if recording_seconds <= 0:
                print(prog + ": the -recording must be greater than zero")
                exit(1)

            continue
    
        # recording_thresold
        if (arg == "-recording_thresold"):
            i += 1
            if i >= argc:
                print(prog + ": Missing thresold number for -recording_thresold")
                exit(1)

            recording_thresold = sys.argv[i]
            i += 1
            if recording_thresold.isdigit() == False:
                print(prog + ": the -recording_thresold must be a number")
                exit(1)

            recording_thresold = int(recording_thresold)
            if recording_thresold <= 0:
                print(prog + ": the -recording_thresold must be greater than zero")
                exit(1)

            continue
        

        # fall through as args do not match any of the options
        if (arg != "-h" and arg != "-help" and arg != "?" and arg != "-?"):
            print(prog + ": bad option: " + arg)
    
        print_options(prog)
        exit(1)
#

def print_options(prog):

    global record_filename
    global echo
    global allow_echo_reverb
    global play_arg
    global recording_seconds
    global recording_thresold

    print(prog + ": options")
    print()
    enabled = " "
    if record_filename == "":
        enabled = "not "
    print("    -record " + record_filename + enabled + "enabled")
    print("        -record filename specifies the wav file to create.")
    print("         this file will be played when activity is detected.")
    print()
    enabled = ""
    if echo == False:
        enabled = "not "
    print("    -echo " + enabled + "enabled")
    print("        -echo specifies that recordered audio will be echoed.")
    print("         as audio is detected it will be echoed.")
    print()
    enabled = ""
    if allow_echo_reverb == False:
        enabled = "not "
    print("    -allow_echo_reverb " + enabled + "enabled")
    print("        -allow_echo_reverb specifies that the echo will be.")
    print("         able to echo itself - reverberation.")
    print()
    print("    -play " + str(play_arg))
    print("        -play files specifies the wave files that will be")
    print("          played when sound detection occurs.")
    print()
    print("    -recording_seconds " + str(recording_seconds))
    print("        -recording_seconds specifies the number of seconds that")
    print("          will be recorded in operations -record and -echo.")
    print()
    print("    -recording_thresold " + str(recording_thresold))
    print("        -recording_thresold specifies the audio volume required")
    print("          to trigger audio detection.")
    print()
#

if __name__=="__main__":

    global audio
    global play_files
    global play_list
    global play_index
    play_list = []
    play_index = 0
    play_arg = "files"
    play_files = []

    parse_args()
    initialize()

    if record:
        wb = record_wave(record_filename)
        play_list.append(wb)
        play = True

    if len(play_files) > 0:
        for f in play_files:
            wb = wave_buffer()
            wb.load_file(f)
            play_list.append(wb)
            play = True

    print("Starting the listening processes:")

    # Set up the threads - user exit and listen for detection
    threads = []

    t = Thread(target=user_exit, args=())
    time.sleep(0.2)
    t.start()
    threads.append(t)

    t = Thread(target=listen, args=())
    time.sleep(0.2)
    t.start()
    threads.append(t)

    # Wait for the thread to exit - does not happen - exit by entering q
    for t in threads:
        t.join()

    audio.terminate()
