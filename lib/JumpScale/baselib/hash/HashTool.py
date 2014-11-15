from __future__ import with_statement
from JumpScale import j

class HashTool:
    def hashDir(self,rootpath):
        """
        walk over all files, calculate md5 and of sorted list also calc md5 this is the resulting hash for the dir independant from time and other metadata (appart from path)
        """
        paths=j.system.fs.listFilesInDir(rootpath,recursive=True,followSymlinks=False)        
        if paths==[]:
            return "",""
        paths2=[]
        for path in paths:
            path2=path.replace(rootpath,"") 
            if path2[0]=="/":
                path2=path2[1:]
            paths2.append(path2)
        paths2.sort()
        out=""
        for path2 in paths2:
            realpath=j.system.fs.joinPaths(rootpath,path2)
            if not j.system.platformtype.isWindows() or not j.system.windows.checkFileToIgnore(realpath):
#                print "realpath %s %s" % (rootpath,path2)
                hhash=j.tools.hash.md5(realpath)
                out+="%s|%s\n"%(hhash,path2)
        return j.base.byteprocessor.hashMd5(out),out        

import hashlib
import zlib

def _hash_funcs(alg):
    '''Function generator for hashlib-compatible hashing implementations'''
    template_data = {'alg': alg.upper(), }

    def _string(s):
        '''Calculate %(alg)s hash of input string

        @param s: String value to hash
        @type s: string

        @returns: %(alg)s hash hex digest of the input value
        @rtype: string
        '''
        if isinstance(s, unicode):
            s = s.encode('utf-8')
        impl = hashlib.new(alg, s)
        return impl.hexdigest()

    # _string.__doc__ = _string.__doc__ % template_data

    def _fd(fd):
        '''Calculate %(alg)s hash of content available on an FD

        Blocks of the blocksize used by the hashing algorithm will be read from
        the given FD, which should be a file-like object (i.e. it should
        implement C{read(number)}).

        @param fd: FD to read
        @type fd: object

        @returns: %(alg)s hash hex digest of data available on C{fd}
        @rtype: string
        '''
        impl = hashlib.new(alg)
        # We use the blocksize used by the hashing implementation. This will be
        # fairly small, maybe this should be raised if this ever becomes an
        # issue
        blocksize = impl.block_size

        while True:
            s = fd.read(blocksize)
            if not s:
                break
            impl.update(s)
            # Maybe one day this will help the GC
            del s

        return impl.hexdigest()

    # _fd.__doc__ = _fd.__doc__ % template_data

    def _file(path):
        '''Calculate %(alg)s hash of data available in a file

        The file will be opened in read/binary mode and blocks of the blocksize
        used by the hashing implementation will be read.

        @param path: Path to file to calculate content hash
        @type path: string

        @returns: %(alg)s hash hex digest of data available in the given file
        @rtype: string
        '''
        with open(path, 'rb') as fd:
            return _fd(fd)

    # _file.__doc__ = _file.__doc__ % template_data

    return _string, _fd, _file

__all__ = list()

# List of all supported algoritms
SUPPORTED_ALGORITHMS = ['md5', 'sha1', 'sha256', 'sha512', ]

# For every supported algorithm, create the associated hash functions and add
# them to the module globals
_glob = globals()
for _alg in SUPPORTED_ALGORITHMS:
    _string, _fd, _file = _hash_funcs(_alg)
    _glob[_alg] = _string
    _glob['%s_fd' % _alg] = _fd
    _glob['%s_file' % _alg] = _file

    __all__.append(_alg)
    __all__.append('%s_fd' % _alg)
    __all__.append('%s_file' % _alg)


# CRC32 is not supported by hashlib
def crc32(s):
    '''Calculate CRC32 hash of input string

    @param s: String value to hash
    @type s: string

    @returns: CRC32 hash of the input value
    @rtype: number
    '''
    return zlib.crc32(s)

def crc32_fd(fd):
    '''Calculate CRC32 hash of content available on an FD

    Blocks of the blocksize used by the hashing algorithm will be read from
    the given FD, which should be a file-like object (i.e. it should
    implement C{read(number)}).

    @param fd: FD to read
    @type fd: object

    @returns: CRC32 hash of data available on C{fd}
    @rtype: number
    '''
    data = fd.read()
    value = crc32(data)
    del data
    return value

def crc32_file(path):
    '''Calculate CRC32 hash of data available in a file

    The file will be opened in read/binary mode and blocks of the blocksize
    used by the hashing implementation will be read.

    @param path: Path to file to calculate content hash
    @type path: string

    @returns: CRC32 hash of data available in the given file
    @rtype: number
    '''
    with open(path, 'rb') as fd:
        return crc32_fd(fd)

SUPPORTED_ALGORITHMS.append('crc32')
__all__.extend(('crc32', 'crc32_fd', 'crc32_file', ))

SUPPORTED_ALGORITHMS = tuple(SUPPORTED_ALGORITHMS)

for alg in SUPPORTED_ALGORITHMS:
    setattr(HashTool, '%s_string' % alg,staticmethod(_glob[alg]))
    setattr(HashTool, alg, staticmethod(_glob['%s_file' % alg]))