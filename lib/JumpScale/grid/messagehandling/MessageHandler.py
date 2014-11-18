
import sys

from JumpScale import j
from .LogHandlerDB import LogHandlerDB

import sys
import simplejson
# import zmq
import struct
import zlib
import pickle


# MESSAGETYPES
# 1:log
# 2:signal
# 3:errorcondition
# 4:alert
# 5:stat


class MessageHandler:

    def __init__(self):
        """
        for doc see messagehandler part in doc section of jumpscale repo
        """
        self.localLogServerEnabled = False
        self.start = 0
        self._client = None
        self._silentRetry = False
        self.queue = False  # when true will queue to local FS
        self.loghandlerdb = LogHandlerDB()
        if len(j.application.whoAmIBytestr) != 6:
            raise RuntimeError("Cannot start messagehandler, the whoAmiBytestr on j.application should be 6 bytes")

    def data2Message(self, ttype, data):
        """
        @param data is already compressed/serialzed data block
        @param ttype is 1:log, 2:signal, 3:ec, 4:alert, 5:perfinfo, 6:raw
                                         type : 10 = uncompressed, json
                                         type : 11 = uncompressed, cpickle
                                         type : 12 = compressed, json
                                         type : 13 = compressed, cpickle
        @return 4byte_sizepacket,4byte_epoch,4byte_grid_id,4byte_nodeid,4byte_pid,1byteDataType,crcOfData,data
        """
        # print len(data)
        # print "who:%s" % len(j.application.whoAmIBytestr)
        # print "crc:%s" % zlib.crc32(data)
        dataLength = len(data)
        if dataLength == 0:
            raise RuntimeError('Couln\'t format message, data length is 0')
        ttype = struct.pack("B", ttype)
        crc = zlib.crc32(data)
        # 25 is length of everything before the data
        msg = struct.pack("I", dataLength + 25) + struct.pack("I", 0) +\
            j.application.whoAmIBytestr + ttype + struct.pack("i", crc) + data

        return msg

    def getRPCMessage(self, appname, actorname, instance, methodname, data, timeout=0,
                      sync=True, serializertype=11):
        """
        JSModelid= appname,actorname,modelname    (use the commas)
        data = dict with data (can be used to create JSModel from) or a var dict
        timeout = in seconds how long the call can take, 0 is not specified
        @param serializertype:
          12 = compressed & json
          13 = compressed & cpickle
          10 = json
          11 = cpickle
        """
        data2 = {}
        data2["app"] = appname
        data2["actor"] = actorname
        data2["method"] = methodname
        data2["inst"] = instance
        data2["timeout"] = timeout
        data2["data"] = data
        data2["sync"] = sync
        if serializertype == 11:
            return self.data2Message(11, pickle.dumps(data2))
        else:
            raise NotImplementedError()

        return self.data2Message()

    def getMessageSize(self, message):
        # @TODO: Document.
        return struct.unpack('I', message[0:4])[0]

    def getMessageType(self, message):
        # @TODO: Document.
        typeIdStr = struct.unpack('B', message[20])[0]
        return int(typeIdStr)
        # return o.enumerators.MessageServerMessageType.getByLevel(typeId)  #@REMARK do not use this, too slow

    def getErrorConditionMessage(self, errorconditionObject):
        # protocol see http://confluence.incubaid.com/display/SHAREDPROJ/Protocol
        obj = simplejson.dumps(errorconditionObject.obj2dict())
        return self.data2Message(3, obj)

    def redirectStdOutStdErrorToLogger(self, yesno):
        if yesno:
            print("REDIRECT STD & STERR to LOGGER")
            from JumpScale.core.logging.RedirectStreams import redirectStreams
            redirectStreams(hideoutput=False)
        else:
            # print "stdout to stderror are not redirected"
            if "_stdout_ori" in sys.__dict__:
                sys.stdout = sys._stdout_ori
            # else:
            #    print "WARNING could not find original stdout"
            if "_stderr_ori" in sys.__dict__:
                sys.stderr = sys._stderr_ori
            else:
                sys.stderr = sys.stdout
            #   print "WARNING could not find original stderror"
            print("restored redirection")

    def connect2localLogserver(self, reconnect=False):

        self.localLogServerEnabled = True
        self._context = zmq.Context(1)

        self._client = self._context.socket(zmq.REQ)
        self._client.connect("tcp://127.0.0.1:7777")

        self._poll = zmq.Poller()
        self._poll.register(self._client, zmq.POLLIN)

        self.start = j.base.time.getTimeEpoch()
        self._silentRetry = False

        if not self.ping():
            self._client = None
        else:
            if not reconnect:
                self.redirectStdOutStdErrorToLogger(False)
                self._monkeyPatch()

    def queueMessage(self, message):
        path = j.system.fs.joinPaths(j.dirs.varDir, "messagequeue", j.application.appname)
        j.system.fs.createDir(path)
        path = "%s/%s.queue" % (path, int(round(j.base.time.getTimeEpoch() / 300, 0) * 300))
        j.system.fs.writeFile(path, message, True)  # will append to file

    def resendQueue(self, applicationName=None):
        """
        will read the queue and try to resend
        """
        def resend(message):
            return self.sendMessage(self, message, retries=1, ignoreError=False, queue=False)
        self.processQueue(resend, applicationName=applicationName, removeWhenDone=True)

    def unPackMessageSeries(self, content):
        """
        unpack text to series of messages
        #format is concatenation of
        4byte_sizepacket,4byte_epoch,4byte_grid_id,4byte_nodeid,4byte_pid,1byteDataType,crcOfData,data
        @return [[dtype,length,epoch,gid,nid,pid,data]]
        """

        result = []
        while content != "":
            length = struct.unpack("I", content[0:4])[0]
            dtype = struct.unpack("B", content[20])[0]
            epoch, gid, nid, pid = struct.unpack("IIII", content[4:20])
            crc = struct.unpack("i", content[21:25])[0]
            data = content[25:length]
            if zlib.crc32(data) != crc:
                raise RuntimeError("Could not decode data from message, crc was not valid, data:\n%s" % data)
            content = content[length:]
            result.append([dtype, length, epoch, gid, nid, pid, data])
        # I LEAVE THIS CODE TO SHOW HOW how it is constructed (documentation)
        # while content:
            # [size|unknown|epoch|gid|nid|pid|logType|crc|data]
            # [4|1|4|4|4|4|1|4] => 26
            # size = struct.unpack('I', content[0:4])[0]
            # epoch = struct.unpack('I', content[5:9])[0]
            # gid = struct.unpack('I', content[9:13])[0]
            # nid = struct.unpack('I', content[13:17])[0]
            # pid = struct.unpack('I', content[17:21])[0]
            # logType = struct.unpack('B', content[21:22])[0]
            # crc = struct.unpack('i', content[22:26])[0]
            # data = content[26:size]
            # crcCheck = zlib.crc32(data)
            # if crc != crcCheck:
                # raise RuntimeError('Could not unpack message series, crc invalid')

            # result.append([logType, size, epoch, gid, nid, pid, data])
            # content = content[size:]

        return result

    def unPackMessage(self, message):
        """
        unpack 1 message
        #format is
        4byte_sizepacket,1byte_type,4byte_epoch,4byte_grid_id,4byte_nodeid,4byte_pid,1byteDataType,crcOfData,data
        @return dtype,length,epoch,gid,nid,pid,data
        """
        return self.unPackMessageSeries(message)[0]

    def processQueue(self, method, messageType=0, applicationName=None, removeWhenDone=False):
        """
        read the queue and call method with as param the message
        @param messageType 0 means all types, 1=log,2=signal,3=error,5=stat
        @removeWhenDone if True then when message processed succesfully, remove from queue succesfull means method needs to return True
        """
        if self.ping():
            if applicationName == None:
                applicationName = j.application.appname
            path = j.system.fs.joinPaths(j.dirs.varDir, "messagequeue", applicationName)
            if j.system.fs.exists(path):
                for item in j.system.fs.listFilesInDir(path):
                    contentOut = ""
                    content = j.system.fs.fileGetContents(path)
                    while content != "":
                        length = struct.unpack("I", content[0:4])[0]
                        dtype = struct.unpack("B", content[21])[0]
                        if messageType == 0 or (messageType != 0 and messageType == dtype):
                            result = method(content[0:length])
                            if removeWhenDone and result:
                                content = content[length:]
                    if removeWhenDone:
                        if contentOut == "":
                            # means all processed well
                            j.system.fs.remove(path)
                        else:
                            j.system.fs.writeFile(path, contentOut)

    def ping(self):
        return self.sendMessage("ping", retries=1, queue=False)

    def modifyTimeInMessage(self, message, epoch):
        return message[:5] + struct.pack("I", epoch) + message[9:]

    def sendMessage(self, message, retries=3, ignoreError=False, queue=True):

        def echo2(msg):
            if self._silentRetry == False:
                j.console.echo(msg, log=False)

        if self._client == None:  # if none means logserver is not available
            if self.start + 60 < j.base.time.getTimeEpoch() or ignoreError == False:
                self.connect2localLogserver()  # every 60 sec retry to connect to logserver
                if not self.ping():
                    self._client = None  # could still not connect
            else:
                return False
            if self._client == None and queue and self.queue:
                self.queueMessage(message)
        if self._client != None:
            retries_left = retries
            while retries_left:
                self._client.send(message)
                socks = dict(self._poll.poll(100))  # is request time out in ms
                if socks.get(self._client) == zmq.POLLIN:
                    reply = self._client.recv()
                    if reply == "1":
                        return True
                    else:
                        return False
                else:
                    # Socket is confused. Close and remove it.
                    self._client.setsockopt(zmq.LINGER, 0)
                    self._client.close()
                    self._poll.unregister(self._client)
                    retries_left -= 1
                    if retries_left == 0:
                        echo2("Local Log Server seems to be offline, will not use.")
                        self._client = None
                        self._context.term()
                        return False
                    # Create new connection
                    self._silentRetry = True
                    self.connect2localLogserver(reconnect=True)

    def _monkeyPatch(self):
        j.logger.cleanup = self._notImplemented
        j.logger.logTargets = []
        j.logger.cleanupLogsOnFilesystem = self._notImplemented
        # j.logger.consoleloglevel
        j.logger.clear = self._notImplementedIgnore
        j.logger.decodeLogMessage = self._notImplemented
        # j.logger.maxlevel
        j.logger.close = self._notImplementedIgnore
        j.logger.exception = self._notImplemented
        j.logger.logTargetAdd = self._notImplemented
        j.logger.nolog = False
        j.logger.log = self.log

    def _notImplemented(self, *args, **kwargs):
        raise RuntimeError("Not implemented on messagehandler 6")

    def _notImplementedIgnore(self, *args, **kwargs):
        pass

    def log(self, message, level=5, tags="", dontprint=False, category=""):
        """
        @param category is in dot notation e.g. appserver3.status or system.fs
        """

        try:
            if level < (j.logger.consoleloglevel + 1) and not dontprint and j.application.interactive:
                j.console.echo(message, log=False)
            if j.logger.nolog:
                return
            if level < j.logger.maxlevel + 1:
                # send to logserver
                self.sendMessage(self.data2Message(1, "%s,%s,%s" % (level, category, message)), 1, True)

        except Exception as e:
            print("HAVE SERIOUS BUG IN LOGGER 4 MESSAGEHANDLER 6\n")
            print(e)
            import pdb
            pdb.Pdb().set_trace(None)
            # pdb.pm()

    def sendSignal(self, signalcategory, jumpscaletags=None):
        if jumpscaletags == None:
            jumpscaletags = ""
        self.sendMessage(self.data2Message(2, "%s,%s" % (signalcategory, jumpscaletags)), 3)

    def sendErrorConditionObject(self, errorConditionObject):
        """
        send errorcondtion object from jumpscale 6 to local logserver
        """
        self.sendMessage(self.getErrorConditionMessage(errorConditionObject), 3)

    def sendStat(self, category, stat):
        msg = "%s,%s" % (signalcategory, jumpscaletags)
        self.sendMessage(self.data2Message(5, msg), 3)
