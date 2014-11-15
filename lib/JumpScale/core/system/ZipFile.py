

'''The ZipFile class provides convenience methods to work with zip archives'''

import sys
import os.path
import zipfile

from JumpScale import j
from JumpScale.core.baseclasses import BaseEnumeration, BaseType

#NOTE: We use this enumeration so we can add zip file creation and others
#later on. This enumeration is used when constructing a new ZipFile object,
#which allows us to do (eg) 'exists' checking when a zip file should be read.
class ZipFileAction(BaseEnumeration):
    '''Enumeration of zip file access methods'''
    @classmethod
    def _initItems(cls):
        '''Register enumeration items'''
        cls.registerItem('read')

        cls.finishItemRegistration()


class ZipFile(BaseType):
    '''Handle zip files'''

    path = j.basetype.filepath(doc='Path of the on-disk zip file')
    action = j.basetype.enumeration(ZipFileAction,
                doc='Access method of zip file')

    def __init__(self, path, action=ZipFileAction.READ):
        '''Create a new ZipFile object

        @param path: Path to target zip file
        @type path: string
        @prarm action: Action to perform on the zip file
        @type action: ZipFileAction
        '''
        if not j.basetype.filepath.check(path):
            raise ValueError('Provided string %s is not a valid path' % path)
        if action is ZipFileAction.READ:
            if not j.system.fs.isFile(path):
                raise ValueError(
                        'Provided path %s is not an existing file' % path)
            if not zipfile.is_zipfile(path):
                raise ValueError(
                        'Provided path %s is not a valid zip archive' % path)
            self._zip = zipfile.ZipFile(path, 'r')
            #TODO Make this optional?
            result = self._zip.testzip()
            if result is not None:
                raise RuntimeError('Trying to open broken zipfile, first broken file is %s' % \
                        result)

        else:
            raise ValueError('Invalid action')

        self.path = path
        self.action = action

    def extract(self, destination_path, files=None, folder=None):
        '''Extract all or some files from the archive to destination_path

        The files argument can be a list of names (relative from the root of
        the archive) to extract. If no file list is provided, all files
        contained in the archive will be extracted.

        @param destination_path: Extraction output folder
        @type destination_path: string
        @param files: Filenames to extract
        @type files: iterable
        @param folder: Folder to extract
        @type folder: string
        '''
        if files and folder:
            raise ValueError('Only files or folders can be provided, not both')

        if not files:
            files = self._zip.namelist()

        if folder:
            files = (f for f in files if os.path.normpath(f).startswith(folder))

        #normpath to strip occasional ./ etc
        for f in (os.path.normpath(_f) for _f in files if not _f.endswith('/')):
            dirname = os.path.dirname(f)
            basename = os.path.basename(f)

            outdir = j.system.fs.joinPaths(destination_path, dirname)
            j.system.fs.createDir(outdir)
            outfile_path = j.system.fs.joinPaths(outdir, basename)

            #On Windows we get some \ vs / in path issues. Check whether the
            #provided filename works, if not, retry replacing \ with /, and use
            #this one if found.
            try:
                self._zip.getinfo(f)
            except KeyError:
                if not sys.platform.startswith('win'):
                    raise
                f_ = f.replace('\\', '/')
                try:
                    self._zip.getinfo(f_)
                except KeyError:
                    pass
                else:
                    f = f_

            data = self._zip.read(f)
            #We need binary write
            j.logger.log('Writing file %s' % outfile_path)
            fd = open(outfile_path, 'wb')
            fd.write(data)
            fd.close()
            del data

    def close(self):
        '''Close the backing zip file'''
        self._zip.close()