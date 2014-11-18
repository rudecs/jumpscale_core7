from JumpScale import j
from ftplib import FTP, error_perm
import os

# maybe this could be switched to http://curlftpfs.sourceforge.net/
class FtpFS(object):
    server = None
    path = None
    filename = None
    end_type = None
    username = 'anonymous'
    password = 'user@aserver.com'
    local_file = None
    ftp = None
    is_dir = False
    recursive = False

    def __init__(self,end_type,server,path,username,password,is_dir=False,recursive=False,tempdir=j.dirs.tmpDir, Atype='copy'):
        """
        Initialize connection
        """
        j.logger.log("FtpFS: connection information: server [%s] path [%s] username [%s] password [%s]" % (server,path,username,password))

        self.end_type = end_type
        self.Atype = Atype
        self.server = server
        # what if no path is specified
        self.filename = j.system.fs.getBaseName(path)
        #self.path = path.rstrip(self.filename).lstrip('/')
        self.path = os.path.dirname(path).lstrip('/')
        #j.logger.log("FtpFS: path is %s" % self.path)
        self.local_dir =  j.system.fs.joinPaths(tempdir , j.base.idgenerator.generateGUID())
        self.local_file = j.system.fs.joinPaths(self.local_dir , self.filename)
        self.tempdir=tempdir
        j.system.fs.createDir(self.local_dir)

        self.is_dir = is_dir
        self.recursive = recursive

        if is_dir == False:
            j.logger.log("FtpFS: copying filename [%s] path [%s]" % (self.filename,self.path))
        else:
            j.logger.log("FtpFS: copying to local directory [%s] from path [%s]" % (self.local_dir,self.path))

        self.username = username
        self.password = password

    def _connect(self, dontCD=False):
        try:
            self.ftp = FTP(self.server)
            #self.ftp.set_debuglevel(2)
            self.ftp.connect()
            self.ftp.set_pasv(True)
            if self.username != None and self.password != None:
                self.ftp.login(self.username,self.password)
            else:
                self.ftp.login()
        except:
            raise RuntimeError('Failed to login on ftp server [%s] credentials login: [%s] pass [%s]' % (self.server,self.username,self.password))
        # change to correct directory
        if not dontCD:
            path = self.path.lstrip(os.sep).split(os.sep)
            for directory in path:
                try:
                    self.ftp.cwd(directory)
                except Exception as e:
                    self.ftp.mkd(directory)
                    self.ftp.cwd(directory)


    def exists(self):
        """
        Checks file or directory existance
        """

        self._connect(dontCD=True)

        try:
            self.ftp.cwd(self.path)

            if self.is_dir:
                return True
        except error_perm as error:
            if error.message.startswith('550'):
                return False
            else:
                raise error

        if not self.is_dir:
            try:
                self.ftp.sendcmd("MDTM %(fileName)s" % {'fileName': self.filename})
                return True
            except error_perm as error:
                if error.message.startswith('550'):
                    return False
                else:
                    raise error


    def upload(self,uploadPath):
        """
        Store file
        """
        self._connect()
        j.logger.log("FtpFS: uploading [%s] to FTP server" % uploadPath)
        if self.is_dir:
            f = j.system.fs.listFilesInDir(uploadPath)
            f += j.system.fs.listDirsInDir(uploadPath)
    #                d = j.system.fs.listDirsInDir(uploadPath,self.recursive)
            for file in f:
                j.logger.log("Checking file [%s]" % file)
                if j.system.fs.isDir(file):
                    self.handleUploadDir(file,uploadPath)
                else:
                    remotefile = j.system.fs.getBaseName(file)
                    self.storeFile(remotefile,file)
        else:
            if j.system.fs.getBaseName(self.local_file) == '':
                remotefile = j.system.fs.getBaseName(uploadPath)
            else:
                remotefile = self.filename

            self.storeFile(remotefile,uploadPath)

    def download(self):
        """
        Download file
        """
        self._connect()
        # FIXME: make sure the original file name is kept
        # should return path to which file was downloaded
        if self.is_dir:
            j.logger.log("FtpFS: downloading dir [%s]" % self.path)
            listing = []
            remote_file_list = self.ftp.retrlines('LIST', listing.append)
            for l in listing:
                t = l.split()
                name = t[-1:]
                j.logger.log("Checking t [%s] with name [%s]" % (t,name))
                if len(name) > 0:
                    if t[0].startswith('d'): #WARNING: dirty-hack alarm!
                        ldir = j.system.fs.joinPaths(self.ftp.pwd(), name[0])
                        self.handleDownloadDir(ldir)
                    elif t[0].startswith('l'):
                        j.logger.log("FtpFS: symlink on FTP (skipping)")
                    else: # it's a normal file
                        j.logger.log("FtpFS: normal file")
                        #rdir = '/'.join([self.local_dir , self.path])
                        rdir = j.system.fs.joinPaths(self.local_dir , self.path)
                        j.system.fs.createDir(rdir)
                        self.retrieveFile(name[0],self.path,rdir)
                else:
                    j.logger.log("FtpFS: skipping [%s]" % name)
            return self.local_dir
        else:
            self.retrieveFile(self.filename,self.path,self.local_file)
            return self.local_file

    def cleanup(self):
        """
        Cleanup of ftp connection
        """
        self.ftp.quit()
        j.system.fs.removeDirTree(self.local_dir)

    def retrieveFile(self,file,dir,dest):
        """
        Ftp copying file
        """
        if self.is_dir:
            lfile = j.system.fs.joinPaths(dest, file)
        else:
            lfile = self.local_file
        j.logger.log("FtpFS: retrieving [%s] from dir [%s] to [%s]" % (file, dir,lfile))
        self.ftp.retrbinary('RETR %s' % file, open(lfile, 'wb').write)

    def storeFile(self,file,uploadPath):
        """
        Ftp upload file
        """
        j.logger.log("FtpFS: storing [%s] from [%s]" % (file,uploadPath))
        # print "%s:%s:%s %s %s"%(self.server,self.username,self.password,file,uploadPath)
        self.ftp.storbinary('STOR %s' % file, open(uploadPath, 'rb'), 8192)
        size=self.ftp.size(file)
        stat=j.system.fs.statPath(uploadPath)
        if size!=stat.st_size:
            self.ftp.delete(file)
            raise RuntimeError("Could not upload:%s %s, size different, have now deleted"%(file,uploadPath))

    def handleUploadDir(self,dir,upload_path):
        """
        Ftp handle a upload directory
        """
        self._connect()
        j.logger.log("FtpFS: handleUploadDir [%s]" % dir)
        dname = j.system.fs.getBaseName(dir)
        j.logger.log("FtpFS: dirname is %s and upload path %s" % (dname, upload_path))
        fname =  dir.replace(upload_path, '')
        previous_dir = '/'.join(['/' , self.path])
        #creating directory on FTP
        j.logger.log("FtpFS: mkd and cwd to [%s] (previous dir %s)" % (fname,previous_dir))
        self.ftp.mkd(fname)
        #self.ftp.cwd(fname)

        f = j.system.fs.listFilesInDir(dir)
        f += j.system.fs.listDirsInDir(dir)
#       d = j.system.fs.listDirsInDir(uploadPath,self.recursive)
        for file in f:
            j.logger.log("Checking file [%s]" % file)
            if j.system.fs.isDir(file):
                self.handleUploadDir(file,upload_path)
            else:
                remotefile = j.system.fs.getBaseName(file)
                self.ftp.cwd(fname)
                self.storeFile(remotefile,file)
                self.ftp.cwd(previous_dir)

    def handleDownloadDir(self,dirname):
        """
        Ftp handle a download directory
        """
        self._connect()
        j.logger.log("FtpFS: handleDownloadDir [%s]" % dirname)
        rdir = '/'.join([self.local_dir , dirname])
        j.logger.log("FtpFs: handleDownloadDir - creating local [%s]" % rdir)
        j.system.fs.createDir(rdir)
        self.ftp.cwd(dirname)

        listing = []
        remote_file_list = self.ftp.retrlines('LIST', listing.append)
        for l in listing:
            t = l.split()
            name = t[-1:]
            j.logger.log("Checking t [%s] with name [%s]" % (t,name))
            if len(name) > 0:
                if t[0].startswith('d'): #WARNING: dirty-hack alarm!
                    ldir = j.system.fs.joinPaths(self.ftp.pwd(), name[0])
                    self.handleDownloadDir(ldir)
                elif t[0].startswith('l'):
                    j.logger.log("FtpFS: symlink on FTP (skipping)")
                else: # it's a normal file
                    j.logger.log("FtpFS: normal file, attempting to retrieve file [%s] to location [%s]" % (name[0], rdir))
                    self.retrieveFile(name[0],self.path,rdir)
            else:
                j.logger.log("FtpFS: skipping [%s]" % name)

        previous_dir = dirname.rstrip(j.system.fs.getBaseName(dirname))
        self.ftp.cwd(previous_dir)

    def list(self):
        """
        List files in dir
        """
        self._connect()
        dir_content = []
        j.logger.log("list: Returning list of FTP directory [%s]" % self.path)
        listing = []
        self.ftp.retrlines('LIST', listing.append)
        for l in listing:
            t = l.split()
            name = t[-1:][0]
            dir_content.append(name)

        return dir_content