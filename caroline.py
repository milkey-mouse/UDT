# -*- coding: cp1252 -*-
import pyaudio
import numpy as np
import pyfftw
import cStringIO as StringIO
import winsound
import base64
import string
import array
import time
import math
import wave
import sys
import os

#use high pass filter at 15000

basefreq = 17000

rbf = raw_input("Select band start (17000 default): ")

if rbf != 0:
    try:
        basefreq = int(rbf)
    except:
        pass

mbase = "ascii"
echars = list((string.ascii_lowercase + " " + string.digits + string.punctuation).replace("~", "") + "~")
binsize = 100

rmb = raw_input("Select message base (options: ascii, 32, 64) (ascii default): ").lower()

if rmb == "32":
    mbase = "32"
    echars = list((string.ascii_uppercase + "234567= ").replace("~", "") + "~")
    #binsize = 200
elif rmb == "64":
    mbase = "64"
    echars = list((string.ascii_letters + string.digits + "+/= ").replace("~", "") + "~")
    #binsize = 150

pdr = raw_input("Enter duration (estimate distance) (default 0.2 seconds): ")

pduration = 0.2 # seconds
if pdr != "":
    try:
        pduration = float(pdr)
    except:
        pass
sampleRate = float(160 * 1000)
dataSize = 2 # 2 bytes because of using signed short integers => bit depth = 16

chunklen = 0.01
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 160 * 1000
chunk = int(RATE * chunklen)

def send_message(inp):
    if mbase == "ascii":
        inp = inp.lower()
    elif mbase == "32":
        inp = base64.b32encode(inp)
    elif mbase == "64":
        inp = base64.b64encode(inp)
    if mbase != "ascii":
        ninp = ""
        pchr = ""
        for char in list(inp):
            if pchr == char:
                ninp += " "
            ninp += char
            pchr = char
        inp = ninp
    inp = "~" + inp[:1] + inp
    duration = pduration * len(inp)
    numSamples = int(sampleRate * pduration)
    data = array.array('h')
    for char in list(inp):
        if char in string.whitespace:
            char = " "
        if char in echars:
            sys.stdout.write(char)
            charsub = echars.index(char) * binsize
            freq = basefreq + charsub
            numSamplesPerCyc = (sampleRate / freq)
            for i in range(numSamples):
                sample = 32767 * math.sin(math.pi * 2 * (i % numSamplesPerCyc) / numSamplesPerCyc)
                data.append(int(sample))
    fstr = StringIO.StringIO()
    f = wave.open(fstr, 'w')
    try:
        f.setparams((1, dataSize, sampleRate, int(sampleRate * duration), "NONE", "Uncompressed"))
        f.writeframes(data.tostring())
    finally:
        f.close()
    print "Playing wav file..."
    winsound.PlaySound(fstr.getvalue(), winsound.SND_MEMORY) # | winsound.SND_ASYNC

def Pitch(signal):
    signal = np.fromstring(signal, 'Int16');
    crossing = [math.copysign(1.0, s) for s in signal]
    index = find(np.diff(crossing));
    f0=round(len(index) *RATE /(2*np.prod(len(signal))))
    return f0;

lastfreq1 = 0

lastshown = 0

wavef = False

alg = "fft"

ralg = raw_input("Select algorithm (zc is faster, fft is better) (default fft): ")

if ralg == "zc":
    alg = "zc"

if wavef:
    wf = wave.open("chat.wav", 'rb')
else:
    p = pyaudio.PyAudio()
    stream = p.open(format = FORMAT, channels = CHANNELS, rate = RATE, input = True, frames_per_buffer = chunk)

returned = True

future = time.time()

curtext = ""

lastfailed = False

if alg == "zc":
    while True:
        try:
            if wavef:
                data = wf.readframes(chunk)
            else:
                data = stream.read(chunk)
            Frequency=Pitch(data)
            if Frequency > 16500:
                rfreq = round((Frequency - basefreq) / binsize)
                if abs(Frequency - lastfreq1) <= 20 and lastshown != rfreq:
                    rchar = echars[int(rfreq)].replace("ƒ", " ")
                    if not (mbase != "ascii" and rchar == " "):
                        sys.stdout.write(rchar)
                        curtext += rchar
                    now = time.time()
                    future = now + 1
                    returned = False
                    lastshown = rfreq
                lastfreq1 = Frequency
            else:
                if time.time() > future and returned == False:
                    returned = True
                    sys.stdout.write("\n")
                    if mbase == "32":
                        dcm = base64.b32decode(curtext.strip())
                    elif mbase == "64":
                        dcm = base64.b64decode(curtext.strip())
                    if lastfailed == False:
                        print dcm
                    elif dcm.startswith("~"):
                        print dcm[1:]
                        lastfailed = False
                    curtext = ""
        except:
            pass
else:
    lastdone = -1
    binstart = (basefreq / 100) - 1
    binend = binstart + len(echars) + 1
    fftsize = chunk #each bin will be 10 Hz
    print "Sampling background noise",
    bgnoise = []
    secs = 4
    seclen = secs / chunklen
    for i in np.arange(0,secs,chunklen):
        if ((i/seclen) * 1000)%1 == 0: 
             sys.stdout.write(".")
        try:
            waveform = np.fromstring(stream.read(chunk), 'Int16')
            spectrum = np.abs(pyfftw.interfaces.numpy_fft.rfft(waveform[:fftsize]))[binstart:]
            specarg = spectrum.argmax()
            bgnoise.append(round(spectrum[specarg]))
        except:
            pass
    print "Done!"
    print "Averaging for threshold...",
    threshold = float(int(sum(bgnoise) / len(bgnoise))) + 200000
    print threshold
    while True:
        try:
            waveform = np.fromstring(stream.read(chunk), 'Int16')
            spectrum = np.abs(pyfftw.interfaces.numpy_fft.rfft(waveform[:fftsize]))[binstart:binend]
            spectrum[spectrum < threshold] = 0
            specarg = spectrum.argmax()
            if spectrum[specarg] == 0:
                if time.time() > future and returned == False:
                    returned = True
                    sys.stdout.write("\n")
                    if mbase == "32":
                        dcm = base64.b32decode(curtext.strip())
                    elif mbase == "64":
                        dcm = base64.b64decode(curtext.strip())
                    else: #ascii
                        dcm = curtext.strip()
                    print dcm
                    if dcm.startswith("~"):
                        print "Message already repeated. Not repeating message."
                    print "Repeating message..."
                    send_message(dcm)
                    print "Done."
                    curtext = ""
                continue
            if specarg == lastdone and specarg != lastshown:
                rchar = echars[specarg - 1].replace("ƒ", " ")
                if not (mbase != "ascii" and rchar == " "):
                    sys.stdout.write(rchar)
                    curtext += rchar
                now = time.time()
                future = now + 1
                returned = False
                lastshown = specarg
            lastdone = specarg
        except TypeError, e:
            print "Error with message, will not transmit: ",
            print str(e)
            curtext = ""
        except IOError, e: #most likely for an unready sound device
            pass
