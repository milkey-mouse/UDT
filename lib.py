

MIN_SIG = 17000
MAX_SIG = 19000
BIN_SIZE = math.floor((MAX_SIG - MIN_SIG) / 32)

def getSignal(num):
    if num == None || !isinstance(num, int) || int < 0 || int > 31:
        raise Exception("Invalid signal")
    return MIN_SIG + BIN_SIZE * num

def translate():

def snd(msg):
    if msg == None || !isinstance(msg, str):
        raise Exception("Could not send type " + type(msg))
    
