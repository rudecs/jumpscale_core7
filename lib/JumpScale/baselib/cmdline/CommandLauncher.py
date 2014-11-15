# <License type="Sun Cloud BSD" version="2.2">
#
# Copyright (c) 2005-2009, Sun Microsystems, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# 3. Neither the name Sun Microsystems, Inc. nor the names of other
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY SUN MICROSYSTEMS, INC. "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL SUN MICROSYSTEMS, INC. OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# </License>

import sys,os
import time
import threading
from JumpScale import j

class CommandLauncher(threading.Thread):
    cmd= None ##string 
    workingdir= None ##string
    output= None ##string
    name= None ##string
    setDaemon= None ##bool

    def __init__(self,cmd,workingdir,name="",setDaemon=False):
        """contructor
        @param cmd: command to launch
        @param workingdir: working directory
        @param name: command name
        @param setDaemon: True if the cmd should start a daemon
        """
        self.cmd=cmd
        self.workingdir=workingdir
        if name<>"":
            self.name=name
        threading.Thread.__init__(self)
        if setDaemon:
            self.setDaemon=True

    def run ( self ):
        """Run the command launcher"""
        os.chdir(self.workingdir)
        resultcode=j.system.process.executeAsync(self.cmd, redirectStreams=False)



if __name__ == '__main__':
    cl=CommandLauncher("xserver.bat","t:/utils/xserver","xserver")
    cl.start()
