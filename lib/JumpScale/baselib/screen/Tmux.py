from JumpScale import j
import time
import os
class Tmux:
    
    def __init__(self):
        self.screencmd="tmux"
    
    def createSession(self,sessionname,screens,user=None):
        """
        @param name is name of session
        @screens is list with nr of screens required in session and their names (is [$screenname,...])
        """
        j.system.platform.ubuntu.checkInstall("tmux","tmux")
        self.killSession(sessionname)
        if len(screens)<1:
            raise RuntimeError("Cannot create screens, need at least 1 screen specified")

        env = os.environ.copy()
        env.pop('TMUX', None)
        cmd="%s new-session -d -s %s -n %s" % (self.screencmd, sessionname, screens[0])
        if user!=None:
            cmd = "sudo -u %s -i %s"%(user,cmd)
        j.system.process.run(cmd, env=env)
        # now add the other screens to it
        if len(screens) > 1:
            for screen in screens[1:]:
                cmd="tmux new-window -t '%s' -n '%s'" % (sessionname, screen)
                if user!=None:
                    cmd = "sudo -u %s -i %s"%(user,cmd)
                j.system.process.execute(cmd)

    def executeInScreen(self,sessionname,screenname,cmd,wait=0, cwd=None, env=None,user="root",tmuxuser=None):
        """
        @param sessionname Name of the tmux session
        @type sessionname str
        @param screenname Name of the window in the session
        @type screenname str
        @param cmd command to execute
        @type cmd str
        @param wait time to wait for output
        @type wait int
        @param cwd workingdir for command only in new screen see newscr
        @type cwd str
        @param env environment variables for cmd onlt in new screen see newscr
        @type env dict
        """
        env = env or dict()
        envstr = ""
        for name, value in env.items():
            envstr += "export %s=%s\n" % (name, value)

        self.createWindow(sessionname, screenname,user=tmuxuser)
        pane = self._getPane(sessionname, screenname,user=tmuxuser)
        env = os.environ.copy()
        env.pop('TMUX', None)

        if envstr!="":
            cmd2="tmux send-keys -t '%s' '%s\n'" % (pane,envstr)
            if tmuxuser!=None:
                cmd2 = "sudo -u %s -i %s"%(tmuxuser,cmd2)        
            j.system.process.run(cmd2, env=env)


        if user!="root":
            cmd="cd %s;%s"%(cwd,cmd)
            sudocmd="su -c \"%s\" %s"%(cmd,user)
            cmd2="tmux send-keys -t '%s' '%s' ENTER" % (pane,sudocmd)
        else:
            # if cmd.find("'")<>-1:
            #     cmd=cmd.replace("'","\\\'")  
            if cmd.find("$")!=-1:
                cmd=cmd.replace("$","\\$")                              
            cmd2="tmux send-keys -t '%s' \"%s;%s\" ENTER" % (pane,"cd %s"%cwd,cmd)
            print(cmd2)
        if tmuxuser!=None:
            cmd2 = "sudo -u %s -i %s"%(tmuxuser,cmd2)
        j.system.process.run(cmd2, env=env)

        time.sleep(wait)
        if wait and j.system.fs.exists(ppath):
            resultcode=j.system.fs.fileGetContents(ppath).strip()
            j.system.fs.remove(ppath)
            if not resultcode or int(resultcode)>0:
                raise RuntimeError("Could not execute %s in screen %s:%s, errorcode was %s" % (cmd,sessionname,screenname,resultcode))
        elif wait:
            j.console.echo("Execution of %s  did not return, maybe interactive, in screen %s:%s." % (cmd,sessionname,screenname))

    def getSessions(self,user=None):
        cmd = 'tmux list-sessions -F "#{session_name}"'
        if user!=None:
            cmd = "sudo -u %s -i %s"%(user,cmd)
        exitcode, output = j.system.process.execute(cmd, dieOnNonZeroExitCode=False)
        if exitcode != 0:
            output = ""
        return [ name.strip() for name in output.split() ]

    def getPid(self, session, name,user=None):
        cmd = 'tmux list-panes -t "%s" -F "#{pane_pid};#{window_name}" -a' % session
        if user!=None:
            cmd = "sudo -u %s -i %s"%(user,cmd)
        exitcode, output = j.system.process.execute(cmd, dieOnNonZeroExitCode=False)
        if exitcode>0:
            return None
        for line in output.split():
            pid, windowname = line.split(';')
            # print "%s '%s'"%(pid,windowname)
            if windowname == name:
                return int(pid)
        return None

    def getWindows(self, session, attemps=5,user=None):
        result = dict()
        
        cmd = 'tmux list-windows -F "#{window_index}:#{window_name}" -t "%s"' % session
        if user!=None:
            cmd = "sudo -u %s -i %s"%(user,cmd)
        exitcode, output = j.system.process.execute(cmd, dieOnNonZeroExitCode=False)
        if exitcode != 0:
            return result
        for line in output.split():
            idx, name = line.split(':', 1)
            result[int(idx)] = name
        return result

    def createWindow(self, session, name,user=None):
        if session not in self.getSessions(user=user):
            return self.createSession(session, [name],user=user)
        windows = self.getWindows(session,user=user)
        if name not in list(windows.values()):
            cmd="tmux new-window -t '%s:' -n '%s'" % (session, name)
            if user!=None:
                cmd = "sudo -u %s -i %s"%(user,cmd)
            j.system.process.execute(cmd)

    def logWindow(self, session, name, filename,user=None):
        pane = self._getPane(session, name,user=user)        
        cmd = "tmux pipe-pane -t '%s' 'cat >> \"%s\"'" % (pane, filename)
        if user!=None:
            cmd = "sudo -u %s -i %s"%(user,cmd)
        j.system.process.execute(cmd)

    def windowExists(self, session, name,user=None):
        if session in self.getSessions(user=user):
            if name in list(self.getWindows(session,user=user).values()):
                return True
        return False

    def _getPane(self, session, name,user=None):
        windows = self.getWindows(session,user=user)
        remap = dict([ (win, idx) for idx, win in windows.items() ])
        result = "%s:%s" % (session, remap[name])
        return result

    def killWindow(self, session, name,user=None):
        try:
            pane = self._getPane(session, name,user=user)
        except KeyError:
            return # window does nt exist
        cmd = "tmux kill-window -t '%s'" % pane
        if user!=None:
            cmd = "sudo -u %s -i %s"%(user,cmd)
        j.system.process.execute(cmd, dieOnNonZeroExitCode=False)

    def killSessions(self,user=None):
        cmd="tmux kill-server"
        if user!=None:
            cmd = "sudo -u %s -i %s"%(user,cmd)
        j.system.process.execute(cmd,dieOnNonZeroExitCode=False) #todo checking
        
    def killSession(self,sessionname,user=None):
        cmd="tmux kill-session -t '%s'"  % sessionname
        if user!=None:
            cmd = "sudo -u %s -i %s"%(user,cmd)
        j.system.process.execute(cmd,dieOnNonZeroExitCode=False) #todo checking

    def attachSession(self,sessionname, windowname=None,user=None):
        if windowname:
            pane = self._getPane(sessionname, windowname,user=user)
            cmd="tmux select-window -t '%s'"  % pane
            if user!=None:
                cmd = "sudo -u %s -i %s"%(user,cmd)
            j.system.process.execute(cmd,dieOnNonZeroExitCode=False)
        cmd="tmux attach -t %s" % (sessionname)
        if user!=None:
            cmd = "sudo -u %s -i %s"%(user,cmd)
        j.system.process.executeWithoutPipe(cmd)
