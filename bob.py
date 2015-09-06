# -*- coding: cp1252 -*-


import pyaudio
import numpy as np
import math, wave, sys, string, time, base64
import pyfftw

chunklen = 0.01
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 160 * 1000
chunk = int(RATE * chunklen)


def Pitch(signal):
    signal = np.fromstring(signal, 'Int16');
    crossing = [math.copysign(1.0, s) for s in signal]
    index = find(np.diff(crossing));
    f0=round(len(index) *RATE /(2*np.prod(len(signal))))
    return f0;

lastfreq1 = 0

basefreq = 17000

rbf = raw_input("Select band start (17000 default): ")

if rbf != 0:
    try:
        basefreq = int(rbf)
    except:
        pass

lastshown = 0

wavef = False

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

ignore = False

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
                    if (not (mbase != "ascii" and rchar == " ")) and ignore == False:
                        if curtext == "" and rchar == "~":
                            ignore = True
                        else:
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
                    ignore = False
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
                    if lastfailed == False:
                        print dcm
                    elif dcm.startswith("~"):
                        print dcm[1:]
                        lastfailed = False
                    ignore = False
                    curtext = ""
                continue
            if specarg == lastdone and specarg != lastshown:
                rchar = echars[specarg - 1].replace("ƒ", " ")
                if (not (mbase != "ascii" and rchar == " ")) and ignore == False:
                    if curtext == "" and rchar == "~":
                        ignore = True
                    else:
                        sys.stdout.write(rchar)
                        curtext += rchar
                now = time.time()
                future = now + 1
                returned = False
                lastshown = specarg
            lastdone = specarg
        except TypeError, e:
            print "Error decoding message, will look for repeaters"
            curtext = ""
            lastfailed = True
        except IOError, e: #most likely for an unready sound device
            pass
