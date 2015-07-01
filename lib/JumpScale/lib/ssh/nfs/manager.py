import os
import re

from StringIO import StringIO
from fabric.api import settings


EXPORTS_FILE = '/etc/exports'

EXPORT_OPT_REGEXT = re.compile('^(?:([\w/]+)|"([\w\s/]+)")\s+(.+)$')
CLIENT_OPT_REGEXT = re.compile('\s*([^\(]+)\(([^\)]+)\)')


class NFSError(Exception):
    pass


class NFSFactory(object):
    def get(self, con):
        return NFS(con)


class NFSExport(object):
    def __init__(self, path):
        self._path = path
        self._clients = []

    @property
    def path(self):
        return self._path

    @property
    def clients(self):
        return self._clients

    def addClient(self, name='*', options='rw,sync'):
        name = name.replace(' ', '')
        options = options.replace(' ', '')

        self._clients.append((name, options))

    def removeClient(self, name):
        name = name.replace(' ', '')
        for i in range(len(self._clients) - 1, -1, -1):
            if self._clients[i][0] == name:
                self._clients.pop(i)

    def __str__(self):
        buf = StringIO()
        buf.write('"%s"' % self._path)
        for client in self._clients:
            buf.write(' %s(%s)' % client)

        return buf.getvalue()

    def __repr__(self):
        return str(self)


class NFS(object):
    def __init__(self, con):
        self._con = con
        self._exports = None

    def _load(self):
        exports = []
        with settings(abort_exception=NFSError):
            content = self._con.file_read(EXPORTS_FILE)
            lineparts = []
            for linepart in content.split(os.linesep):
                linepart = linepart.strip()
                if linepart == '' or linepart.startswith('#'):
                    continue

                lineparts.append(linepart)

                if linepart.endswith('\\'):
                    lineparts.append(linepart)
                    continue

                line = ' '.join(lineparts)
                lineparts = []

                match = EXPORT_OPT_REGEXT.match(line)
                if not match:
                    raise NFSError("Invalid line '%s'" % line)

                path = match.group(1) or match.group(2)
                export = NFSExport(path)
                exports.append(export)

                opts = match.group(3)
                for clientm in re.finditer(CLIENT_OPT_REGEXT, opts):
                    export.addClient(clientm.group(1), clientm.group(2))
        self._exports = exports

    @property
    def exports(self):
        if self._exports is None:
            self._load()
        return self._exports

    def add(self, path):
        export = NFSExport(path)
        self.exports.append(export)
        return export

    def delete(self, path):
        for i in range(len(self.exports) - 1, -1, -1):
            export = self.exports[i]
            if export.path == path:
                self.exports.pop(i)

    def erase(self):
        self._exports = []

    def commit(self):
        buf = StringIO()
        for export in self.exports:
            buf.write("%s\n" % export)

        with settings(abort_exception=NFSError):
            self._con.file_write(EXPORTS_FILE, buf.getvalue(), mode=644)
            self._con.upstart_reload('nfs-kernel-server')
