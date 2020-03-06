__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

import pyaudio
import wave
import os

# TODO replace with LoZ sounds

def minor_error_sound():
    play(os.path.join('sounds', 'crowd_boo.wav'))

def error_sound():
    play(os.path.join('sounds', 'air_horn.wav'))

def complete_sound():
    play(os.path.join('sounds', 'tada.wav'))

def warning_sound():
    play(os.path.join('sounds', 'siren.wav'))

def play(soundfile):
    CHUNK = 1024

    wf = wave.open(soundfile, 'rb')

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(CHUNK)

    while data != '':
        stream.write(data)
        data = wf.readframes(CHUNK)

    stream.stop_stream()
    stream.close()

    p.terminate()
