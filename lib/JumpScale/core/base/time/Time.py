

from JumpScale import j
import time
import struct

TIMES = {'s': 1,
 'm': 60,
 'h': 3600,
 'd': 3600 * 24,
 'w': 3600 * 24 * 7
}


class Time:
    """
    generic provider of time functions
    lives at j.base.time
    """
    def getTimeEpoch(self):
        '''
        Get epoch timestamp (number of seconds passed since January 1, 1970)
        '''
        try:
            return j.core.appserver6.runningAppserver.webserver.epoch  #@todo P3 (check if working)
        except:
            pass
        timestamp = int(time.time())
        return timestamp

    def getTimeEpochBin(self):
        '''
        Get epoch timestamp (number of seconds passed since January 1, 1970)
        '''
        return struct.pack("<I",self.getTimeEpoch())


    def getLocalTimeHR(self):
        '''Get the current local date and time in a human-readable form'''
        #timestamp = time.asctime(time.localtime(time.time()))
        timestr=self.formatTime(self.getTimeEpoch())
        return timestr

    def getLocalTimeHRForFilesystem(self):
        #@todo check if correct implementation
        return time.strftime("%d_%b_%Y_%H_%M_%S", time.gmtime())
    
    def formatTime(self,epoch,formatstr='%Y/%m/%d %H:%M:%S',local=True):
        '''
        Returns a formatted time string representing the current time

        See http://docs.python.org/lib/module-time.html#l2h-2826 for an
        overview of available formatting options.

        @param format: Format string
        @type format: string

        @returns: Formatted current time
        @rtype: string
        '''
        epoch=float(epoch)
        if local:
            timetuple=time.localtime(epoch)
        else:
            timetuple=time.gmtime(epoch)
        timestr=time.strftime(formatstr,timetuple)
        return timestr

    def epoch2HRDate(self,epoch,local=True):
        return self.formatTime(epoch,'%Y/%m/%d',local)
        
    def epoch2HRDateTime(self,epoch,local=True):
        return self.formatTime(epoch,'%Y/%m/%d %H:%M:%S',local)
        
    def epoch2HRTime(self,epoch,local=True):
        return self.formatTime(epoch,'%H:%M:%S',local)
        

    def getMinuteId(self,epoch=None):
        """
        is # min from jan 1 2010
        """
        if epoch==None:
            epoch=time.time()
        if epoch<1262318400.0:
            raise RuntimeError("epoch cannot be smaller than 1262318400, given epoch:%s"%epoch)
        
        return int((epoch-1262318400.0)/60.0)

    def getHourId(self,epoch=None):
        """
        is # hour from jan 1 2010
        """
        return int(self.getMinuteId(epoch)/60)

    def fiveMinuteIdToEpoch(self,fiveMinuteId):
        return fiveMinuteId*60*5+1262318400

    def get5MinuteId(self,epoch=None):
        """
        is # 5 min from jan 1 2010
        """
        return int(self.getMinuteId(epoch)/5)

    def getDayId(self,epoch=None):
        """
        is # day from jan 1 2010
        """
        return int(self.getMinuteId(epoch)/(60*24))


    def getDeltaTime(self, txt):
        """
        only supported now is -3m, -3d and -3h (ofcourse 3 can be any int)
        and an int which would be just be returned
        means 3 days ago 3 hours ago
        if 0 or '' then is now
        """
        txt = txt.strip()
        unit = txt[-1]
        if txt[-1] not in TIMES.keys():
            raise RuntimeError("Cannot find time, needs to be in format have time indicator %s " % TIMES.keys())
        value = float(txt[:-1])
        return value * TIMES[unit]


    def getEpochAgo(self,txt):
        """
        only supported now is -3m, -3d and -3h  (ofcourse 3 can be any int)
        and an int which would be just be returned
        means 3 days ago 3 hours ago
        if 0 or '' then is now
        """
        if txt==None or str(txt).strip()=="0":
            return self.getTimeEpoch()
        return self.getTimeEpoch() + self.getDeltaTime(txt)

    def getEpochFuture(self,txt):
        """
        only supported now is +3d and +3h  (ofcourse 3 can be any int)        
        +3d means 3 days in future
        and an int which would be just be returned
        if txt==None or 0 then will be 1 day ago
        """
        if txt==None or str(txt).strip()=="0":
            return self.getTimeEpoch()
        return self.getTimeEpoch() + self.getDeltaTime(txt)
                
    def HRDatetoEpoch(self,datestr,local=True):
        """
        convert string date to epoch
        Date needs to be formatted as 16/06/1988
        """
        if datestr.strip()=="":
            return 0
        try:
            datestr=datestr.strip()
            return time.mktime(time.strptime(datestr, "%d/%m/%Y"))
        except:
            raise ValueError ("Date needs to be formatted as \"16/06/1981\", also check if date is valid, now format = %s" % datestr)
        
