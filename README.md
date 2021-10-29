Audio Scare Alarm Using Pyaudio
===============================
This is an audio detector that plays wav files when noise is detected.  My daughter had an insight into alarms when she was eight years old.  She posited that car and home alarms that rang a siren were not effective.  She thought that having the alarm make a scary noise would work best.  To that end we connected a PIR motion detector to a toy "speak and play" device.  To recreate this many years later, I did a similar hack by adding a PIR device to a Raspberry PI - easy.  That was not that satisfying as it was difficult to run that on laptop and desktop devices.  Instead of using a PIR device with this code we listen for above level audio - works great.  We use a USB Logitech camera/microphone - better audio input quality than most laptops and one can move the mic around.

To get this to run on Linux machines one needs to add pyaudio:
```
   sudo apt-get install portaudio19-dev
   sudo pip3 install pyaudio
```
Install on windows 10:
```
   https://www.python.org/downloads/
   pip install pipwin
   pipwin install pyaudio
```
Install on Macs:
```
   xcode-select --install
   brew remove portaudio
   brew install portaudio
   pip3 install pyaudio
```
One can run the code with CLI commands like the following:
```
   python3 detector.py -play wav.d/german-shephard-daniel_simon.wav -recording_thresold 3000 
```
You can get a list of options by adding a question mark (i.e. ?) to the command line.  -echo option will echo bits of audio that are detected.  The -record option will record a new wav file.

A good source of scary wav files can be found on https://soundbible.com.

You are on your own, but you knew that.
