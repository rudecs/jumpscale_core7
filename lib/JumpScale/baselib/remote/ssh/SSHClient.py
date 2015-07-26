import warnings
# warnings.filterwarnings('ignore', r'.*sha.*')

from JumpScale import j

import base64
from binascii import hexlify
import select
import socket
import sys

import paramiko
# try:
#     import interactive
# except ImportError:
#     from . import interactive


class SSHClient:

    client = None  # object of type client

    def __init__(self, host="", username="root", password=None, timeout=10,port=22,pkey=None,keypath=None):
        self.host = host
        self.port = 22
        self.timeout = timeout
        self.client = None
        # self.keypasswd=keypasswd
        self.port=port

        print "SSH connect: host:%s username:%s port:%s keypath:%s"%(host,username,port,keypath)

        # # now connect
        # try:
        #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     sock.connect((self.host, self.port))
        # except Exception as e:
        #     msg='*** Connect to ssh server failed: ' + str(e)
        #     traceback.print_exc()
        #     j.events.inputerror_critical(msg)

        # t = paramiko.Transport(sock)
        # try:
        #     t.start_client()
        # except paramiko.SSHException:
        #     j.events.inputerror_critical('*** SSH negotiation failed.')


        # if keypath!=""
        #     if keypasswd!="":
        #         paramiko.RSAKey.from_private_key_file(path,passwd=self.keypasswd)
        #     else:
        #         paramiko.RSAKey.from_private_key_file(path)
        # elif password!="":
        #     self.client.connect(self.host, self.port, self.username, self.password, timeout=self.timeout)
        # else:
        #     agent = paramiko.Agent()
        #     agent_keys = agent.get_keys()
        #     if len(agent_keys) == 0:
        #         return j.events.inputerror_critical("Cannot find ssh agent keys, and there is no passwd or keyfile specified.")
        
        #     for key in agent_keys:
        #         print('Trying ssh-agent key %s' % hexlify(key.get_fingerprint()))
        #         try:
        #             transport.auth_publickey(username, key)
        #             print('... success!')
        #             return
        #         except paramiko.SSHException:
        #             print('... nope.')

        self.client = paramiko.SSHClient()        
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.client.connect(self.host, port=self.port, username=username, password=password, pkey=pkey, key_filename=keypath, \
            timeout=timeout, allow_agent=True, look_for_keys=True, compress=False, sock=None, gss_auth=False, gss_kex=False, \
            gss_deleg_creds=False, gss_host=None, banner_timeout=None)
        

    def execute(self, command, dieOnError=True):
        """
        only works for unix
        Execute a command on the SSH server.  Wait till output done.
        @raise error: if the server fails to execute the command
        return returncode,stdout,stderr
        """
        command2 = command + " ; if [ $? -ne 0 ] ; then echo ***ERROR*** 1>&2 ; fi ; echo \"***DONE***\""
        j.logger.log("Execute ssh command %s on %s" % (command, self.host))
        stdin, channelFileStdOut, channelFileStdErr = self.client.exec_command(command2)
        myOut = ""
        myErr = ""
        while (not channelFileStdOut.channel.eof_received) or (not channelFileStdErr.channel.eof_received):
            if channelFileStdOut.channel.recv_ready():
                tmp = (channelFileStdOut.channel.recv(1024))
                j.logger.log("ssh %s out:%s" % (self.host, tmp), 6)
                myOut += tmp
            if channelFileStdErr.channel.recv_stderr_ready():
                tmp = (channelFileStdErr.channel.recv_stderr(1024))
                j.logger.log("ssh %s err:%s" % (self.host, tmp), 6)
                myErr += tmp
        tmp = channelFileStdOut.read()
        j.logger.log("ssh %s out:%s" % (self.host, tmp), 6)
        myOut += tmp
        tmp = channelFileStdErr.read()
        j.logger.log("ssh %s err:%s" % (self.host, tmp), 6)
        myErr += tmp
        if len(myErr.strip()) > 0 and dieOnError:
            raise RuntimeError("Could not execute %s on %s, output was \n%s\n%s\n" % (command, self.host, myOut, myErr))
        else:
            rc=2
        if myOut.find("***DONE***") == -1:
            if dieOnError:
                raise RuntimeError("Did not get all output from executing the SSH command %s" % command)
            rc=1

        myOut=myOut.replace("***DONE***","")
        return rc,myOut, myErr

    def getSFtpConnection(self):
        j.logger.log("Open SFTP connection to %s" % (self.host))
        #t = paramiko.Transport((self.host, self.port))
        #t.connect(username=self.username , password=self.password)
        sftp = paramiko.SFTPClient.from_transport(self.client.get_transport())
        return sftp

    # def _removeRedundantFiles(self, path):
    #     j.logger.log("removeredundantfiles %s" % (path))
    #     files = j.system.fs.listFilesInDir(path, True, filter="*.pyc")
    #     files.extend(j.system.fs.listFilesInDir(path, True, filter="*.pyo"))  # @todo remove other files  (id:6)
    #     for item in files:
    #         j.system.fs.remove(item)

    ##USE j.ssh & linux tools

    # def copyDirTree(self, source, destination="", removeNonRelevantFiles=False):
    #     """
    #     Recursively copy an entire directory tree rooted at source.
    #     The destination directory may already exist; if not, it will be created
    
    #     Parameters:        
    #     - source: string (source of directory tree to be copied)
    #     - destination: string (path directory to be copied to...should not already exist)
    #       if destination no specified will use same location as source
    #     """
    #     if destination == "":
    #         destination = source
    #     dirs = {}
    #     self.executewait("mkdir -p %s" % destination)
    #     ftp = self.getSFtpConnection()
    #     if removeNonRelevantFiles:
    #         self._removeRedundantFiles(source)
    #     files = j.system.fs.listFilesInDir(source, recursive=True)
    #     j.logger.log("Coppy %s files from %s to %s" % (len(files), source, destination), 2)
    #     for filepath in files:
    #         dest = j.system.fs.joinPaths(destination, j.system.fs.pathRemoveDirPart(filepath, source))
    #         destdir = j.system.fs.getDirName(dest)
    #         if destdir not in dirs:
    #             j.logger.log("Create dir %s" % (destdir))
    #             # ftp.mkdir(destdir)
    #             self.executewait("mkdir -p %s" % destdir)
    #             dirs[destdir] = 1
    #         j.logger.log("put %s to %s" % (filepath, dest))
    #         ftp.put(filepath, dest)

    # def _execute(self, command):
    #     """
    #     Execute a command on the SSH server.  A new L{Channel} is opened and
    #     the requested command is executed.  The command's input and output
    #     streams are returned as python C{file}-like objects representing
    #     stdin, stdout, and stderr.

    #     @param command: the command to execute
    #     @type command: str
    #     @return: the stdin, stdout, and stderr of the executing command
    #     @rtype: tuple(L{ChannelFile}, L{ChannelFile}, L{ChannelFile})

    #     @raise SSHException: if the server fails to execute the command
    #     """
    #     return self.client.exec_command(command)

    def logSSHToFile(self, logFile):
        "send ssh logs to a logfile, if they're not already going somewhere"
        paramiko.util.log_to_file(logFile)

    def getOutPut(self, channelFileStdOut, channelFileStdErr):
        myOut = ""
        myErr = ""
        while not channelFileStdOut.channel.eof_received and not channelFileStdErr.channel.eof_received:
            if channelFileStdOut.channel.recv_ready():
                myOut += (channelFileStdOut.channel.recv(1024))
            if channelFileStdErr.channel.recv_stderr_ready():
                myErr += (channelFileStdErr.channel.recv_stderr(1024))
        return myOut, myErr

    def __del__(self):
        """
        Close this SSHClient.
        """
        self.client.close()
