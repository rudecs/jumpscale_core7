from JumpScale import j
from NetworkScanner import NetworkScanner
import multiprocessing
import time
import logging
from Queue import Empty


NUM_WORKERS = 4



def _process(dumper, ip, port, queue, errorqueue):
    logging.info('processing %s:%s' % (ip, port))
    try:
        redis = j.clients.redis.getRedisClient(ip, port)
        now = int(time.time())
        dumper.dump(redis)
        queue.put_nowait((ip, port))
    except Exception:
        logging.exception("Failed to process redis '%s:%s'" % (ip, port))
        errorqueue.put_nowait((ip, port))
    finally:
        # workers must have some rest (1 sec) before moving to next
        # ip to process
        if int(time.time()) - now < 1:
            # process took very short time. Give worker time to rest
            time.sleep(1)

class BaseDumper(object):
    def __init__(self, cidr, ports=[6379], scaninterval=300):
        logging.root.setLevel(logging.INFO)

        self._cidr = cidr
        self._scaninterval = scaninterval
        self._scanner = NetworkScanner(cidr, ports)
        self._circulation = set()


    def update_queue(self, queue):
        candidates = self._scanner.scan()
        for ip, ports in candidates.items():
            for port in ports:
                item = (ip, port)
                if item not in self._circulation:
                    self._circulation.add(item)
                    queue.put_nowait((ip, port))

    def start(self, workers=NUM_WORKERS):
        manager = multiprocessing.Manager()
        queue = manager.Queue()
        errorqueue = manager.Queue()
        self.update_queue(queue)

        pool = multiprocessing.Pool(workers)
        scantime = time.time()

        while True:
            if scantime + self._scaninterval < time.time():
                self.update_queue(queue)
                scantime = time.time()

            while not errorqueue.empty():
                erroritem = errorqueue.get()
                if erroritem in self._circulation:
                    self._circulation.remove(erroritem)
            try:
                ip, port = queue.get(timeout=5)
                pool.apply_async(_process, (self, ip, port, queue, errorqueue))
            except Empty:
                # queue is empty carry on
                pass

    @property
    def cidr(self):
        return self._cidr

    def dump(self, redis):
        """
        Dump, gets a redis connection. It must process the queues of redis until there is no more items to
        process and then immediately return.

        :param redis: redis connection
        :return:
        """
        """
        :param redis:
        :return:
        """
        raise NotImplementedError
