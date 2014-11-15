
import sys
from JumpScale import j

original_stdout = None
original_stderr = None

def canWrite(f):
    return hasattr(f, 'closed') and not f.closed

class _Redirector:

    def __init__(self, stream, hideoutput, loglevel):
        self.loglevel = loglevel
        self.savedstream = stream
        self.hideoutput = hideoutput
        self.stringBuff = ''
 
    def write(self, string):
        if not self.hideoutput and canWrite(self.savedstream):
            try:
                self.savedstream.write(string)
            except IOError, e:
                j.logger.log("Could not write to stdout: %s" % e, self.loglevel, dontprint=True)
        if j._init_final_called<>False:
            if j.logger.inlog==False:
                if self.stringBuff <> '':
                    j.logger.log(self.stringBuff, self.loglevel,dontprint=True)
                    self.stringBuff=''
                j.logger.log(string, self.loglevel,dontprint=True)

    def flush(self):
        if canWrite(self.savedstream):
            self.savedstream.flush()

    def writelines(self, lines):
        for line in lines:
            self.write(line)
            
    def fileno(self):
        return self.savedstream.fileno()

def isRedirected(stream):
    return isinstance(stream, _Redirector)


def redirectStreams(hideoutput=False, loglevel=4, stdout=True, stderr=True):
    """
    Redirect sys.stdout and sys.stderr to j.logger.
    Original streams are saved as original_stdout and original_stderr in this package
    @hideoutput: boolean indicating whether output must still be sent to original stderr/stdout
    @loglevel: log severity level to be used
    @stdout: boolean indicating whether sys.stdout must be redirected
    @stderr: boolean indicating whether sys.stderr must be redirected
    """
    stdout=False
    stderr=False
    if stdout:
        if not sys.__dict__.has_key("_stdout_ori"):
            sys._stdout_ori = sys.stdout
        sys.stdout = _Redirector(sys.stdout, hideoutput, loglevel)
    
    if stderr:
        if not sys.__dict__.has_key("_stdout_ori"):
            sys._stderr_ori = sys.stderr
        sys.stderr = _Redirector(sys.stdout, hideoutput, loglevel)
        
