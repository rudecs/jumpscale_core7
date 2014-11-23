from JumpScale import j
import re
import os
import time
import pexpect

class Screen:
    
    def __init__(self):
        self.screencmd="byobu"
    
    def createSession(self,sessionname,screens):
        """
        @param name is name of session
        @screens is list with nr of screens required in session and their names (is [$screenname,...])
        """
        j.system.platform.ubuntu.checkInstall("screen","screen")
        j.system.platform.ubuntu.checkInstall("byobu","byobu")
        j.system.process.execute("byobu-select-backend  screen")
        self.killSession(sessionname)
        if len(screens)<1:
            raise RuntimeError("Cannot create screens, need at least 1 screen specified")
        #-dmS means detatch & create 1 screen session 
        cmd="%s -dmS '%s'"%(self.screencmd,sessionname)
        j.system.process.execute(cmd)
        self._do(sessionname, ['title', screens[0]], '0')
        # now add the other screens to it
        if len(screens) > 1:
            for screen in screens[1:]:
                self._do(sessionname, ["screen", "-t", screen])

    def executeInScreen(self,sessionname,screenname,cmd,wait=0):

        from IPython import embed
        print("DEBUG NOW ooo")
        embed()
        
        ppath=j.system.fs.getTmpFilePath()
        ppathscript=j.system.fs.getTmpFilePath()
        script="""
#!/bin/sh
#set -x

check_errs()
{
  # Function. Parameter 1 is the return code
  # Para. 2 is text to display on failure.
  if [ "${1}" -ne "0" ]; then
    echo "ERROR # ${1} : ${2}"
    echo ${1} > %s    
    # as a bonus, make our script exit with the right error code.
    exit ${1}
  fi
}

%s
check_errs $? 
rm -f %s
    """ %(ppath,cmd,ppathscript)
        j.system.fs.writeFile(ppathscript,script)
        if wait!=0:
            cmd2="%s -S %s -p %s -X stuff '%s;echo $?>%s\n'" % (self.screencmd,sessionname,screenname,cmd,ppath)
            
        else:
            cmd2="%s -S %s -p %s -X stuff '%s\n'" % (self.screencmd,sessionname,screenname,cmd)

        print(cmd2)

        j.system.process.execute(cmd2)  
        time.sleep(wait)
        if j.system.fs.exists(ppath):
            resultcode=j.system.fs.fileGetContents(ppath).strip()
            if resultcode=="":
                resultcode=0
            resultcode=int(resultcode)       
            j.system.fs.remove(ppath)
            if resultcode>0:
                raise RuntimeError("Could not execute %s in screen %s:%s, errorcode was %s" % (cmd,sessionname,screenname,resultcode))
        else:
            j.console.echo("Execution of %s  did not return, maybe interactive, in screen %s:%s." % (cmd,sessionname,screenname))
        if j.system.fs.exists(ppath):
            j.system.fs.remove(ppath)
        if j.system.fs.exists(ppathscript):
            j.system.fs.remove(ppathscript)      
            
    def getSessions(self):
        cmd="%s -ls" % self.screencmd
        resultcode,result=j.system.process.execute(cmd,dieOnNonZeroExitCode=False)#@todo P2 need to be better checked
        state="start"
        result2=[]
        for line in result.split("\n"):
            if line.find("/var/run/screen")!=-1:
                state="end"
            if state=="list":                
        #print "line:%s"%line
                if line.strip()!="" and line!=None:
                    line=line.split("(")[0].strip()
                    splitted=line.split(".")
            #print splitted
                    result2.append([splitted[0],".".join(splitted[1:])])
            if line.find("are screens")!=-1 or line.find("a screen")!=-1:
                state="list"
        
        return result2
        
    def listSessions(self):
        sessions=self.getSessions()
        for pid,name in sessions:
            print(("%s %s" % (pid,name)))

    def _do(self, session, cmd, window=None):
        scrcmd = [self.screencmd, '-S', session]
        if window:
            scrcmd += ['-p', window]
        scrcmd += ['-X']
        scrcmd += cmd
        return pexpect.spawn(scrcmd[0], scrcmd[1:]).wait()

    def listWindows(self, session, attemps=5):
        tmpfolder = j.system.fs.getTmpDirPath()
        fl = j.system.fs.joinPaths(tmpfolder, '%n %t %W')
        self._do(session, ['log', 'off'])
        self._do(session, ['logfile', fl])
        with self.attached(session):
            self._do(session, ['log', 'on'])
            self._do(session, ['log', 'off'])
        # somehow this keeps screen bussy which makes it ignore incomming commands
        time.sleep(1)
        files = j.system.fs.listFilesInDir(tmpfolder)
        j.system.fs.removeDirTree(tmpfolder)
        if not files:
            attemps -= 1
            if attemps <=0:
                raise RuntimeError('Failed to get windows')
            return self.listWindows(session, attemps)
        output = files[0]
        output = j.system.fs.getBaseName(output)
        lst = re.split('(\d+)\s', output)
        if lst:
            lst = lst[1:]
        result = dict()
        for idx, data in enumerate(lst[::2]):
            result[int(lst[idx*2])] = lst[idx*2+1].strip()
        return result

    def createWindow(self, session, name):
        if session not in list(dict(self.getSessions()).values()):
            return self.createSession(session, [name])
        windows = self.listWindows(session)
        if name not in list(windows.values()):
            self._do(session, ['screen', '-t', name] )

    def windowExists(self, session, name):
        if session in list(dict(self.getSessions()).values()):
            if name in list(self.listWindows(session).values()):
                return True
        return False

    def attached(self, session):
        class Active(object):
            def __init__(s, session):
                s.session = session
                s.proc = None

            def __enter__(s):
                s.proc = pexpect.spawn(self.screencmd, ['-x', session])

            def __exit__(s, *args):
                if s.proc:
                    s.proc.terminate()
        return Active(session)

    def killWindow(self, session, name):
        if self.windowExists(session, name):
            with self.attached(session):
                self._do(session, ['kill'], name)

    def killSessions(self):
        #@todo P1 is there no nicer way of cleaning screens
        cmd="screen -wipe" 
        j.system.process.execute(cmd,dieOnNonZeroExitCode=False) #@todo P2 need to be better checked
        sessions=self.getSessions()
        for pid,name in sessions:
            try:
                j.system.process.kill(int(pid))
            except:
                j.console.echo("could not kill screen with pid %s" % pid)
        cmd="screen -wipe" 
        j.system.process.execute(cmd,dieOnNonZeroExitCode=False) #todo checking
        
    def killSession(self,sessionname):
        cmd="screen -wipe" 
        j.system.process.execute(cmd,dieOnNonZeroExitCode=False) #todo checking
        sessions=self.getSessions() 
        for pid,name in sessions:
            if name.strip().lower()==sessionname.strip().lower():
                try:
                    j.system.process.kill(int(pid))
                except:
                    j.console.echo("could not kill screen with pid %s" % pid)
        cmd="screen -wipe" 
        j.system.process.execute(cmd,dieOnNonZeroExitCode=False) #todo checking

    def attachSession(self,sessionname):
        #j.system.process.executeWithoutPipe("screen -d -r %s" % sessionname)
        j.system.process.executeWithoutPipe("%s -d -r %s" % (self.screencmd,sessionname))
