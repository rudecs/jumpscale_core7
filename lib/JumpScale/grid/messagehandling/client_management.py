import gevent

from gevent import Timeout
from gevent.queue import Queue
from gevent_zeromq import zmq
from utils import printInDebugMode


class MessageServerClient(object):

    _BACKOFF_INTERVALS = (1, 1, 1, 5, 10, 30, 60)
    _MAX_BUFFER_SIZE = 1000
    _RECEIVE_TIMEOUT = 2

    def __init__(self, address):
        '''
        MessageServerClient constructor.

        @param address: address to send the messages to
        @type address: str
        '''

        self._address = 'tcp://%s' % address
        self._socket = None
        self._context = None

        self._queue = Queue()
        self._processQueueInLoop()

    @property
    def address(self):
        return self._address

    def ping(self):
        '''
        Sends a ping message to the server and checks if it answers.

        @return: True when the server answered, False otherwise
        @rtype: bool
        '''

        return self._send('ping', receiveTimeout=1)

    def send(self, message):
        '''
        Puts a message in the queue and immediately after that yields. This will
        give the worker which is running in a Greenlet the time to process the
        queue.

        @param message: message to send to the server
        @type message: str
        '''

        self._queue.put(message)
        gevent.sleep()

    @property
    def _isConnected(self):
        '''
        Returns a flag that states if the client is connected or not.

        @return: flag that states if the client is connected or not
        @rtype: bool
        '''

        if self._context:
            return not self._context.closed
        else:
            return False

    def _connect(self):
        '''Connects the client if it isn't already'''

        if self._isConnected:
            printInDebugMode('Can\'t connect to %s, already connected'
                             % self._address)
            return

        printInDebugMode('Connecting to %s' % self._address)
        self._context = zmq.Context(2)
        self._socket = self._context.socket(zmq.REQ)
        self._socket.setsockopt(zmq.LINGER, 0)
        self._socket.connect(self._address)
        printInDebugMode('Connected to %s' % self._address)

    def _disconnect(self):
        '''Disconnects the client if it isn't already'''

        if not self._isConnected:
            printInDebugMode('Can\'t disconnect from %s, already disconnected'
                             % self._address)
            return

        printInDebugMode('Disconnecting from %s' % self._address)
        self._socket.close()
        self._context.term()
        printInDebugMode('Disconnected from %s' % self._address)

    def _processQueue(self):
        '''
        Tries to process as many as possible queued messages. A message buffer
        is updated on every attempt. This buffer is then flattened to a single
        message. This reduces the amount of roundtrips with the server.

        When a message is not send succesfully a series of retry attempts will
        be completed before aborting. After every failed attempt the client
        backs off for a fixed amound of seconds.

        @return: True when a part of the queue is succesfully processes, False otherwise
        @rtype: bool
        '''

        maxAttempts = len(self._BACKOFF_INTERVALS) + 1
        isSucces = False
        buffer = list()

        for attempt in range(1, maxAttempts):
            buffer = self._updateBuffer(buffer)
            message = ''.join(buffer)  # The message is actually a batch of messages.

            isSucces = self._send(message)

            if isSucces:
                break
            else:
                interval = self._BACKOFF_INTERVALS[attempt - 1]

                printInDebugMode('''\
Failed to send message to %(address)s in %(attempts)d attempt(s)'
Retrying to send message to %(address)s in %(interval)d seconds'''
                                 % {'address': self._address, 'attempts': attempt,
                                    'interval': interval})

                gevent.sleep(interval)

        if isSucces:
            printInDebugMode('Successfully sent message to %s in %d attempt(s)'
                             % (self._address, attempt))
        else:
            printInDebugMode('Failed to send message to %s in %d attempt(s)'
                             % (self._address, attempt))

        return isSucces

    def _processQueueInLoop(self):
        '''
        Spawns a worker in a Greenlet that processes the queue when possible.
        '''

        def worker():
            while True:
                self._processQueue()

        gevent.spawn(worker)

    def _updateBuffer(self, buffer):
        '''
        Updates a buffer by moving as much messages as possible from the queue
        to the buffer. This method will block if the queue is empty. Once a
        message is put in the queue the buffer will be updated.

        @param buffer: buffer to update
        @type buffer: set()

        @return: updated buffer
        @rtype: set()
        '''

        while len(buffer) < self._MAX_BUFFER_SIZE:
            # The get call on the queue will block until a message is put in the
            # queue.
            message = self._queue.get()
            buffer.append(message)

            if self._queue.empty():
                break

        return buffer

    def _send(self, message, receiveTimeout=_RECEIVE_TIMEOUT):
        '''
        Tries to send a message to the server and waits a fixed amount of
        seconds for it to answer.

        @param message: message to send to the server
        @type message: str

        @param receiveTimeout: max time in seconds in which the server should respond
        @type receiveTimeout: int
        '''

        if not self._isConnected:
            self._connect()

        try:
            self._socket.send(message)
        except Exception, e:
            self._disconnect()
            printInDebugMode('Couldn\'t send message, unexpected exception'
                             ' while sending to server: %s' % e)

        result = None

        timeout = Timeout(receiveTimeout)
        timeout.start()

        try:
            result = self._socket.recv()
        except Timeout, timeoutException:
            if timeoutException == timeout:
                printInDebugMode('Couldn\'t send message, server response timed'
                                 ' out after %d seconds' % receiveTimeout)

            self._disconnect()
        except Exception, e:
            printInDebugMode('Couldn\'t send message, unexpected exception'
                             ' while receiving response from server: %s' % e)
            self._disconnect()
        finally:
            timeout.cancel()

        return result == '1'

    def __del__(self):
        '''
        Makes sure that the client is disconnected properly before being
        deleted.
        '''

        if self._isConnected:
            self._disconnect()


class MessageServerClientFactory(object):

    def get(self, address):
        '''
        Gets an message server client.

        @TODO: Document the format of the address.

        @param address: address the client should send its messages to
        @type address: str
        '''

        return MessageServerClient(address)
