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

pdr = raw_input("Enter duration (estimate distance) (default 0.1 seconds): ")

pduration = 0.1 # seconds
if pdr != "":
    try:
        pduration = float(pdr)
    except:
        pass
sampleRate = float(160 * 1000)
dataSize = 2 # 2 bytes because of using signed short integers => bit depth = 16

while True:
    inp = raw_input("\nSend a message: ")
    #inp = "abcdefghijklmnopqrstuvwxyz 0123456789" #"The newest version of the device has a frequency of approximately 17.4 kHz that can generally be heard only by young people."
    if mbase == "ascii":
        inp = inp.lower().replace("~", "")
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
    inp = inp[:1] + inp
    duration = pduration * len(inp)
    numSamples = int(sampleRate * pduration)
    data = array.array('h')
    #ncl = []
    #for char in list(inp):
    #    ncl.append(echars.index(char))
    #print ncl
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
    #print "\nSaving wav file..."
    #with open("chat.wav", "wb") as chatwav:
    #    chatwav.write(fstr.getvalue())
    print "\nPlaying wav file..."
    winsound.PlaySound(fstr.getvalue(), winsound.SND_MEMORY) # | winsound.SND_ASYNC
    #for char in list(inp):
    #    sys.stdout.write(char)
    #    time.sleep(0.1)
    #print ""
        
