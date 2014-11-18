import argparse
import gevent
import signal
import struct

from gevent import Greenlet, Timeout
from gevent.queue import Queue
from .gevent_zeromq import zmq
from JumpScale.core.InitBase import *
from zmj.core.error import ZMQError
import time

#@todo do not use arakoon to pass information to the commandcenter, integrate with appserver6 to pass info like this (in other words let logserver3 work together in same process space as appserver 6)


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


class MessageForwarder(object):
    #@todo no need to have 2 classes, forwarder & logserver should be the same
    #@todo please use queues in local as well as in forwarder (like it was)

    RETRY_BACKOFF_INTERVALS = [1, 1, 1, 5, 10, 30, 60]
    RECEIVE_TIMEOUT = 2

    def __init__(self, address):
        self._address = 'tcp://%s' % address

        self._socket = None
        self._context = None

    @property
    def address(self):
        return self._address

    def forward(self, message):
        attempts = 0
        isSucces = False

        for interval in self.RETRY_BACKOFF_INTERVALS:
            attempts += 1

            if not self._connected:
                self._connect()

            try:
                self._socket.send(message)
                gevent.with_timeout(self.RECEIVE_TIMEOUT, self._socket.recv)
            except (Timeout, ZMQError):
                self._disconnect()
                self._logForwardFailure(attempts, interval)

                gevent.sleep(interval)
                continue

            isSucces = True
            break

        if isSucces:
            self._log('Successfully forwarded message to %s in %d attempts'
                      % (self._address, attempts))
        else:
            self._log('Failed to forward message to %s in %d attemts'
                      % (self._address, attempts))

    @property
    def _connected(self):
        if self._context:
            return self._context.closed
        else:
            return False

    def _connect(self):
        self._log('Connecting to %s' % self._address)
        self._context = zmq.Context(2)
        self._socket = self._context.socket(zmq.REQ)
        self._socket.connect(self._address)
        self._log('Connected to %s' % self._address)

    def _disconnect(self):
        self._log('Disconnecting from %s' % self._address)
        self._socket.close()
        # self._context.term()
        self._log('Disconnected from %s' % self._address)

    def _log(self, message):
        print(message)

    def _logForwardFailure(self, attempts, interval):
        self._log('''\
Failed to forward message to %(address)s in %(attempts)d attempt(s)'
Retrying to forward message to %(address)s in %(interval)d seconds'''
                  % {'address': self._address, 'attempts': attempts,
                     'interval': interval})

    def __del__(self):
        self._disconnect()


class MessageServer(object):

    FORWARD_MESSAGES_BATCH_SIZE = 100  # @todo queues have been removed this introduced completely different behaviour

    def __init__(self, address, storeLocally):
        self._address = 'tcp://%s' % address
        self._storeLocally = storeLocally

        self._socket = None
        self._messages = Queue()  # @todo there were multiple queues for the 4 styles which is needed because different behaviour required
        self._stats = {
            'received': 0,
            'processed': 0,
            'forwarded': 0,
        }
        self._statsChanged = False
        self._categories = None

        self.epoch = 0

        self.echo = False
        self.forwarders = set()

    def start(self):
        greenlet = Greenlet(self._start)
        greenlet.link_exception(self._logGreenletError)

        TIMER = gevent.greenlet.Greenlet(self._timer)
        TIMER.start()

        # Start and wait until the log server stops (main greenlet).
        greenlet.start()
        greenlet.join()

    def _start(self):
        context = zmq.Context(1)
        self._socket = context.socket(zmq.REP)
        self._socket.bind(self._address)

        self._log('Message server started on %s' % self._address)

        if self.forwarders:
            addresses = [forwarder.address for forwarder in self.forwarders]
            self._log('Message server forwarding to: %s' % ', '.join(addresses))

        gevent.spawn(self._receive)

        while True:
            self._processMessages()

            if self._statsChanged:
                self._statsChanged = False
                self._log(self._stats)

            gevent.sleep(1)

    def _timer(self):
        """
        will remember time every sec
        """
        while True:
            # self.epochbin=struct.pack("I",time.time())
            self.epoch = time.time()
            gevent.sleep(1)

    @property
    def isForwarding(self):
        return len(self.forwarders) > 0

    @property
    def numberMessages(self):  # @todo why properties??? this makes it slower
        return self._messages.qsize()

    def _forward(self, messages):
        for forwarder in self.forwarders:
            message = '\n'.join(messages)

            greenlet = gevent.spawn(forwarder.forward, message)
            greenlet.link_exception(self._logGreenletError)

        self._stats['forwarded'] += len(messages)
        self._statsChanged = True

    def _log(self, message):
        print(message)

    def _logGreenletError(self, greenlet):
        self._log(greenlet.exception)

    def _processErrorMessage(self, message):
        dtype, length, epoch, gid, nid, pid, data = j.core.messagehandler.unPackMessage(message)
        eco = j.errorconditionhandler.getErrorConditionObject(data=j.tools.json.decode(data))

        content = "source/id/level: %s/%s/%s\n" % (eco.getSource(), eco.guid, eco.level)
        content += "error: %s\n" % eco.errormessage
        print(content)

        j.errorconditionhandler.db.store(eco)

    def _processLogMessage(self, message):
        if self.echo:
            self._log(message)

        if self._storeLocally:
            j.core.loghandler.save(message)

    def _processMessages(self):
        forwardMessages = None

        while self.numberMessages > 0:

            message = self._messages.get()
            messageType = struct.unpack('B', message[20])[0]
            messageTypeId = int(messageType)

            message = j.core.messagehandler.modifyTimeInMessage(message, self.epoch)

            if messageTypeId == 1:
                self._processLogMessage(message)
            elif messageTypeId == 2:
                self._processSignalMessage(message)
            elif messageTypeId == 3:
                self._processErrorMessage(message)
            elif messageTypeId == 5:
                self._processStatusMessage(message)
            else:
                self._log('Could not process message, unknown type id %s' % messageTypeId)

            self._stats['processed'] += 1
            self._statsChanged = True

            if self.isForwarding:
                if not forwardMessages:
                    forwardMessages = list()

                forwardMessages.append(message)

                if len(forwardMessages) == self.FORWARD_MESSAGES_BATCH_SIZE \
                        or self.numberMessages == 0:
                    self._forward(forwardMessages)  # @todo this should be the same code as sending a message to the locallogserver

    def _processSignalMessage(self, message):
        raise NotImplementedError()

    def _processStatusMessage(self, message):
        raise NotImplementedError()

    def _receive(self):
        # there were multiple queues, please re-introduce (why did we remove it?)
        while True:
            request = self._socket.recv()

            if request != 'ping':
                self._stats['received'] += 1
                self._statsChanged = True
                self._messages.put(request)

            self._socket.send('1')

if __name__ == '__main__':
    # Prevent gevent  so called zombie processes by calling gevent.shutdown
    # when the SIGQUIT event is raised.
    gevent.signal(signal.SIGQUIT, gevent.shutdown)

    parser = argparse.ArgumentParser(description='Starts the log server.')

    parser.add_argument('-a', '--address', default='127.0.0.1:7777',
                        dest='address', help='Address (ip and port) for this message server')

    parser.add_argument('-c', '--arakoon-client-name', dest='arakoonClientName',
                        help='Arakoon client name to store the categories to')

    parser.add_argument('-e', '--echo', action='store_true', dest='echo',
                        help='Print the log messages when processing them')

    parser.add_argument('-s', '--store-locally', action='store_true',
                        dest='storeLocally', help='Store messages locally to disk')

    parser.add_argument('-f', '--forward-addresses', default=[],
                        dest='forwardAddresses', nargs='*', help='Addresses (ip and port) to '
                        'forward the messages to')

    args = parser.parse_args()

    server = MessageServer(args.address, args.storeLocally)
    server.echo = args.echo

    for address in args.forwardAddresses:
        forwarder = MessageForwarder(address)
        server.forwarders.add(forwarder)

    if args.arakoonClientName:
        client = j.clients.arakoon.getClient(args.arakoonClientName)
        j.core.loghandler.setArakoonClient(client)

    server.start()
