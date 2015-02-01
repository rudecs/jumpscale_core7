from JumpScale import j

descr = """
Creates a targz of the backup under {var directory}/backup/osis/{timestamp}.tgz
"""

organization = "jumpscale"
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
category = "system.backup.osis"
period = 60*60*24
enable = True
async = True
roles = ["admin"]
queue ='io'

def action():
    import JumpScale.grid.osis
    import tarfile
    """
    """
    backuppath = j.system.fs.joinPaths(j.dirs.tmpDir, 'backup', 'osis')
    timestamp = j.base.time.getTimeEpoch()
    timestamp = j.base.time.formatTime(timestamp, "%Y%m%d_%H%M%S")
    try:
        oscl = j.clients.osis.getByInstance('main')
        namespaces = oscl.listNamespaces()
        if j.system.fs.exists(backuppath):
            j.system.fs.removeDirTree(backuppath)
        for namespace in namespaces:
            categories = oscl.listNamespaceCategories(namespace)
            for category in categories:
                if namespace == 'system' and category in ['stats', 'log', 'sessioncache']:
                    continue
                outputpath = j.system.fs.joinPaths(backuppath, namespace, category)
                j.system.fs.createDir(outputpath)
                oscl.export(namespace, category, outputpath)

        #targz
        backupdir = j.system.fs.joinPaths(j.dirs.varDir, 'backup', 'osis')
        j.system.fs.createDir(backupdir)
        outputpath = j.system.fs.joinPaths(backupdir, '%s.tar.gz' % timestamp)
        with tarfile.open(outputpath, "w:gz") as tar:
            tar.add(backuppath)
        j.system.fs.removeDirTree(backuppath)
    except Exception:
        import JumpScale.baselib.mailclient
        import traceback
        error = traceback.format_exc()
        message = '''
OSIS backup at %s failed on %s.%s
Data should have been backed up to %s on the admin node.

Exception:
-----------------------------
%s
-----------------------------
    ''' % (timestamp, j.application.whoAmI.gid, j.application.whoAmI.nid, backuppath, error)
        message = message.replace('\n', '<br/>')
        j.clients.email.send('support@mothership1.com', 'monitor@mothership1.com', 'OSIS backup failed', message)


if __name__ == '__main__':
    action()
