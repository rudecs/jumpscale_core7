import argparse
import gevent
import os
import signal

from client_management import MessageServerClient
from gevent import Greenlet
from gevent.queue import Queue
from gevent_zeromq import zmq
from JumpScale import j


if not q._init_called:
    from JumpScale.core.InitBase import q


# IMPORT INFORMATION
#

# ZMQ::REQ
#
# A socket of type ZMQ::REQ is used by a client to send requests to and
# receive replies from a service. This socket type allows only an
# alternating sequence of send(request) and subsequent recv(reply)
# calls. Each request sent is load-balanced among all services, and each
# reply received is matched with the last issued request.

# When a ZMQ::REQ socket enters an exceptional state due to having reached the
# high water mark for all services, or if there are no services at all, then any
# send() operations on the socket shall block until the exceptional state ends
# or at least one service becomes available for sending; messages are not
# discarded.

# ZMQ::REP
#
# A socket of type ZMQ::REP is used by a service to receive requests from and
# send replies to a client. This socket type allows only an alternating sequence
# of recv(request) and subsequent send(reply) calls. Each request received is
# fair-queued from among all clients, and each reply sent is routed to the
# client that issued the last request.

# When a ZMQ::REP socket enters an exceptional state due to having reached the
# high water mark for a client, then any replies sent to the client in question
# shall be dropped until the exceptional state ends.


# @Todo: Make a queue for each type of message, so that each type of message can
#        have a different way of processing them

# @Todo: Check for performance bottlenecks.

class Stat():

    def __init__(self):
        self.received = 0
        self.processed = 0
        self.forwarded = 0


class Stats():

    def __init__(self):
        self.logs = Stat()
        self.signals = Stat()
        self.errors = Stat()
        self.stats = Stat()


class MessageServer(object):

    DEFAULT_PID_FILE = j.system.fs.joinPaths(j.dirs.pidDir, 'message_server.pid')
    FORWARD_MESSAGES_BATCH_SIZE = 100

    def __init__(self, address, storeLocally, pidFile=None, echo=False):
        self._address = 'tcp://%s' % address
        self.storeLocally = storeLocally
        self._pid = os.getpid()
        self._pidFile = pidFile or self.DEFAULT_PID_FILE
        self.stats = Stats()
        self._socket = None
        self._context = None
        self.logQueue = Queue()
        self.categories = None

        self.echo = echo
        self.forwardAddresses = []
        self.forwardClients = set()

        j.core.messagehandler.epoch = 0

    def start(self):
        print('Starting message server')

        for forwardAddress in self.forwardAddresses:
            client = MessageServerClient(forwardAddress)
            server.forwardClients.add(client)

        self._connect()

        self._storePidInPidFile()

        gevent.core.signal(signal.SIGHUP, self.stop)
        gevent.core.signal(signal.SIGINT, self.stop)
        gevent.core.signal(signal.SIGTERM, self.stop)

        greenlet = Greenlet(self.receiveMessages)
        greenlet.link_exception(self._logGreenletError)

        greenlet2 = Greenlet(self.processLogMessages)
        greenlet2.link_exception(self._logGreenletError)
        greenlet2.start()

        greenlet3 = Greenlet(self._timer)
        greenlet3.link_exception(self._logGreenletError)
        greenlet3.start()

        greenlet.start()

        storeLocallyStr = str(self.storeLocally)
        addresses = [client.address for client in self.forwardClients]
        addressesStr = ', '.join(addresses)

        print('''\
Message server started
listens on: %s
stores locally: %s
forwards to: %s
pid: %d
pid file: %s''' % (self._address, storeLocallyStr, addressesStr, self._pid, self._pidFile))

        # Wait until the log server stops (main greenlet).
        try:
            greenlet.join()
        except KeyboardInterrupt:
            # Ignore this error.
            pass

    def stop(self):
        print('Stopping message server')
        self._disconnect()
        self._removePidFile()
        print('Stopped message server')

    def _connect(self):
        if self._isConnected:
            print('Can\'t connect to %s, already connected' % self._address)
            return

        self._context = zmq.Context(2)
        self._socket = self._context.socket(zmq.REP)
        self._socket.setsockopt(zmq.LINGER, 0)
        self._socket.bind(self._address)

    def _disconnect(self):
        if not self._isConnected:
            print('Can\'t disconnect from %s, already disconnected' % self._address)
            return

        self._socket.close()
        self._context.term()

    @property
    def _isConnected(self):
        if self._context:
            return not self._context.closed
        else:
            return False

    @property
    def isForwarding(self):
        return len(self.forwardClients) > 0

    @property
    def numberQueuedMessages(self):
        return self._messageQueue.qsize()

    def forwardLogMessages(self, messages):
        for client in self.forwardClients:
            client.send(message)

    def _logGreenletError(self, greenlet):
        print(greenlet.exception)

    def _timer(self):
        while True:
            self.epoch = j.base.time.getTimeEpoch()
            j.core.messagehandler.epoch = self.epoch
            gevent.sleep(0.1)

    def processLogMessages(self):
        forwardMessages = ""
        while True:
            gevent.sleep(1)
            message = self.logQueue.get()

            if self.storeLocally:
                j.core.messagehandler.loghandlerdb.save(message)

            if self.echo:
                dtype, length, epoch, gid, nid, pid, data = j.core.messagehandler.unPackMessage(message)
                print(data)

            if self.isForwarding:

                forwardMessages += message

                if len(forwardMessages) > self.FORWARD_MESSAGES_BATCH_SIZE:
                    self.forwardLogMessages(forwardMessages)
                    forwardMessages = ""

            if forwardMessages <> "":
                self._forward(message)

    def processErrorMessage(self, message):
        dtype, length, epoch, gid, nid, pid, data = j.core.messagehandler.unPackMessage(message)
        print data
        return

    def processSignalMessage(self, message):
        return

    def processStatusMessages(self, message):
        return

    def processAllertMessage(self, message):
        return

    def receiveMessages(self):
        # receive from ZMQ
        while True:
            message = self._socket.recv()

            if message != 'ping':

                messageType = j.core.messagehandler.getMessageType(message)
                MessageServerMessageType = j.enumerators.MessageServerMessageType
                if messageType == 1:
                    self.logQueue.put(message)
                elif messageType == 2:
                    self.processSignalMessage(message)
                elif messageType == 3:
                    self.processErrorMessage(message)
                elif messageType == 4:
                    self.processAllertMessage(message)
                elif messageType == 5:
                    self.processStatusMessages(message)
                else:
                    self.raiseError("Did not recognise messagetype %s for message %s" % (messageType, message))

            self._socket.send('1')

    def _removePidFile(self, *args):
        if j.system.fs.exists(self._pidFile):
            pidStr = j.system.fs.fileGetContents(self._pidFile)
            pid = int(pidStr)

            if pid == self._pid:
                j.system.fs.remove(self._pidFile)

    def _storePidInPidFile(self):
        pidStr = str(self._pid)
        j.system.fs.writeFile(self._pidFile, pidStr)

    def raiseError(self, msg):
        print msg

if __name__ == '__main__':
    # Prevent gevent  so called zombie processes by calling gevent.shutdown
    # when the SIGQUIT event is raised.
    gevent.signal(signal.SIGQUIT, gevent.shutdown)

    parser = argparse.ArgumentParser(description='Starts the message server.')

    parser.add_argument('-a', '--address', default='127.0.0.1:7777',
                        dest='address', help='Address (ip and port) for this message server')

    parser.add_argument('-e', '--echo', action='store_true', dest='echo',
                        help='Print the log messages when processing them')

    parser.add_argument('-f', '--forward-addresses', default=[],
                        dest='forwardAddresses', nargs='*', help='Addresses (ip and port) to '
                        'forward the messages to')

    parser.add_argument('-p', '--pid-file',
                        default=MessageServer.DEFAULT_PID_FILE, dest='pidFile',
                        help='Process identifier file path')

    parser.add_argument('-s', '--store-locally', action='store_true',
                        dest='storeLocally', help='Store messages locally to disk')

    args = parser.parse_args()

    server = MessageServer(args.address, args.storeLocally, args.pidFile,
                           args.echo)
    server.echo = args.echo

    for address in args.forwardAddresses:
        server.forwardAddresses.append(address)

    server.start()
