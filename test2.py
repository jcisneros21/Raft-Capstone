#test to make sure weird timer functionality isnt constantly increasing
# the number of threads
import threading

class test:
    def __init__(self):
        self.oldtimer = threading.Timer(3, self.trans)
        self.oldtimer.start()

    def trans(self):
        self.oldtimer = threading.Timer(3, self.trans)
        self.oldtimer.start()
        print(len(threading.enumerate()))

te = test()
