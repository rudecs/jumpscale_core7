

'''The TarFile class provides convenience methods to work with tar archives'''

import tarfile

from JumpScale import j
from JumpScale.core.baseclasses import BaseEnumeration, BaseType

#NOTE: We use this enumeration so we can add tar file creation and others
#later on. This enumeration is used when constructing a new TarFile object,
#which allows us to do (eg) 'exists' checking when a tar file should be read.
class TarFileAction(BaseEnumeration):
    '''Enumeration of tar file access methods'''
    @classmethod
    def _initItems(cls):
        '''Register enumeration items'''
        cls.registerItem('read')

        cls.finishItemRegistration()


#NOTE: When implementing, see documentation on the 'errorlevel' attribute of
#the Python TarFile object
class TarFile(BaseType):
    '''Handle tar files'''

    path = j.basetype.filepath(doc='Path of the on-disk tar file')
    action = j.basetype.enumeration(TarFileAction,
                doc='Access method of tar file')

    def __init__(self, path, action=TarFileAction.READ):
        '''Create a new TarFile object

        @param path: Path to target tar file
        @type path: string
        @prarm action: Action to perform on the tar file
        @type action: TarFileAction
        '''
        if not j.basetype.filepath.check(path):
            raise ValueError('Provided string "%s" is not a valid path' % path)
        if action is TarFileAction.READ:
            if not j.system.fs.isFile(path):
                raise ValueError(
                        'Provided path "%s" is not an existing file' % path)
            if not tarfile.is_tarfile(path):
                raise ValueError(
                        'Provided path "%s" is not a valid tar archive' % path)
            self._tar = tarfile.open(path, 'r')

        else:
            raise ValueError('Invalid action')

        self.path = path
        self.action = action


    def extract(self, destination_path, files=None):
        '''Extract all or some files from the archive to destination_path

        The files argument can be a list of names (relative from the root of
        the archive) to extract. If no file list is provided, all files
        contained in the archive will be extracted.

        @param destination_path: Extraction output folder
        @type destination_path: string
        @param files: Filenames to extract
        @type files: iterable
        '''
        if not self.action is TarFileAction.READ:
            raise RuntimeError('Can only extract archives opened for reading')

        if not j.basetype.dirpath.check(destination_path):
            raise ValueError('Not a valid folder name provided')
        if not j.system.fs.exists(destination_path):
            raise ValueError('Destination folder "%s" does not exist'
                    % destination_path)

        members = list()
        if files:
            all_members = self._tar.getmembers()
            for member in all_members:
                if member.name in files:
                    members.append(member)

        if members:
            self._tar.extractall(destination_path, members)
        else:
            self._tar.extractall(destination_path)

    def close(self):
        '''Close the backing tar file'''
        self._tar.close()

