"""
  raspi-detector.py: Original work Copyright (C) 2021 by Blewett

 This uses a PIR detector input on a raspberry pi to play alarm sounds.

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
import sys
import os
import RPi.GPIO as GPIO
import time
import random
import pyaudio
import wave

#
# globals
#
CHUNK = 1024
global audio

sounds = [
    # "wav.d/Air-Plane-Ding-Corsica-SoundBible.com.wav",
    # "wav.d/Doberman-Pincher-Daniel-Simion-SoundBible.com.wav",
    # "wav.d/Dog-Growling-Mike-Koenig-SoundBible.com.wav",
    "wav.d/german-shephard-Daniel-Simon-SoundBible.com.wav",
    # "wav.d/Police-Scanner-Chatter-PoliceScan-SoundBible.com.wav",
    # "wav.d/Police-Scanner-ScanMan-SoundBible.com.wav",
    "wav.d/scared.wav",
    # "wav.d/shotgun-mossberg590-short-RA_The_Sun_God-SoundBible.com.wav",
    "wav.d/warrant.wav"
]
sounds_length = len(sounds)
marks = [False] * sounds_length
count = 0

def play_wave(filename):
    global audio

    wf = wave.open(filename, 'rb')

    wave_data = []
    data = 1
    while data:
        data = wf.readframes(CHUNK)
        wave_data.append(data)

    wf.close()

    stream = audio.open(format = audio.get_format_from_width(wf.getsampwidth()),
                        channels = wf.getnchannels(),
                        rate = wf.getframerate(),
                        output = True)

    stream.start_stream()

    i = 0
    while i < len(wave_data[i]):
        stream.write(wave_data[i])
        i = i + 1

    # stream.stop_stream()
    stream.close()
#

def play_sound():
    global sounds
    global sounds_length
    global marks
    global count

    i = random.randint(0,sounds_length - 1)
    while marks[i] == True:
        i = random.randint(0,sounds_length - 1)
        continue

    marks[i] = True
    count += 1

    s = sounds[i]
    print(s)
    play_wave(s)
    print(s + ": done")

    if count == sounds_length:
        marks = [False] * sounds_length
        count = 0
#

def nullStderr():
    global old_sys_stderr

    sys.stderr.flush()
    old_sys_stderr = sys.stderr
    err = open('/dev/null', 'a+')
    os.dup2(err.fileno(), sys.stderr.fileno())

def restoreStderr():
    os.dup2(sys.stdout.fileno(), sys.stderr.fileno())

if __name__=="__main__":

    global audio
    global old_sys_stderr

    print("Ignoring error messages!");
    nullStderr()
    audio = pyaudio.PyAudio()
    restoreStderr()
    print("Error messages restored!");
    print()

    print("Enter ^C to exit:");

    SENSOR_PIN = 4
 
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SENSOR_PIN, GPIO.IN)
 
    def my_callback(channel):
        play_sound()

    try:
        GPIO.add_event_detect(SENSOR_PIN , GPIO.RISING, callback=my_callback)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print ("Finish...")

    GPIO.cleanup()
#
