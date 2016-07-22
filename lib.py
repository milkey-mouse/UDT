

MIN_SIG = 17000
MAX_SIG = 19000
BIN_SIZE = math.floor((MAX_SIG - MIN_SIG) / 32)

def snd(msg = "")
    if type(msg) != "<type 'str'>":
        
