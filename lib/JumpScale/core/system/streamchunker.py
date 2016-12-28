
blocksize = 1024 ** 2


class AbstractStream(object):
    def __init__(self):
        self.closed = False

    def __iter__(self):
        return self

    def next(self):
        try:
            return self.read(size=1024 ** 2)
        except EOFError:
            raise StopIteration

    def close(self):
        self.closed = False


class ChunkReader(AbstractStream):
    def __init__(self, file, chunksize):
        super(ChunkReader, self).__init__()
        self.file = file
        self.chunksize = chunksize
        self.position = 0
        self.finished = False

    def read(self, size=None):
        if self.position == self.chunksize:
            raise EOFError("Reached end of chunk")
        if size is None:
            size = self.chunksize - self.position
        elif size + self.position > self.chunksize:
            size = self.chunksize - self.position
        self.position += size
        data = self.file.read(size)
        if data == '':
            self.finished = True
        return data


class StreamChunker(object):
    def __init__(self, file, chunksize=10 * 1024 ** 2):
        self.file = file
        self.chunksize = chunksize
        self.position = 0
        self._lastchunk = None

    def __iter__(self):
        return self

    def next(self):
        if self._lastchunk and self._lastchunk.position != self.chunksize:
            raise RuntimeError("Can not continue with next chunk if previous chunk is not fully read")
        elif self._lastchunk and self._lastchunk.finished:
            raise StopIteration
        self._lastchunk = ChunkReader(self.file, self.chunksize)
        return self._lastchunk


class StreamUnifier(AbstractStream):
    def __init__(self, streams):
        super(StreamUnifier, self).__init__()
        self._streams = iter(streams)
        self._activestream = next(self._streams)

    def read(self, size=None):
        if size is None:
            size = blocksize
        try:
            data = self._activestream.read(size)
            if data == '':
                raise EOFError("End of current stream")
            return data
        except EOFError:
            try:
                self._activestream = next(self._streams)
                return self.read(size)
            except StopIteration:
                return ''
