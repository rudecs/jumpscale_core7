from JumpScale import j
import time

class TIMER:
    @staticmethod
    def start():
        TIMER.clean()
        TIMER._start=time.time()

    @staticmethod
    def stop(nritems=0,log=True):        
        TIMER._stop=time.time()
        TIMER.duration=TIMER._stop-TIMER._start
        if nritems>0:
            TIMER.nritems=float(nritems)
            if TIMER.duration>0:
                TIMER.performance=float(nritems)/float(TIMER.duration)
        if log:
            TIMER.result()
    
    @staticmethod
    def clean():
        TIMER._stop=0.0
        TIMER._start=0.0
        TIMER.duration=0.0
        TIMER.performance=0.0
        TIMER.nritems=0.0
    
    @staticmethod
    def result():
        print("duration:%s"%TIMER.duration)
        print("nritems:%s"%TIMER.nritems)
        print("performance:%s"%TIMER.performance)


j.base.timer=TIMER
