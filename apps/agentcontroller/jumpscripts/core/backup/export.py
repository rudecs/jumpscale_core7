
from JumpScale import j
import os

descr = """
Exports database
"""
organization = "jumpscale"
author = "hamdy.farag@codescalers.com"
license = "bsd"
version = "1.0"
category = "osis.backup"
order = 1
enable = True
async = True
log = False
roles = []

OUTPUTDIR  = '/opt/jumpscale7/backup'
NAMESPACES = ['cloudbroker', 'vfw']

def action():
    osiscl = j.clients.osis.get()
    if not os.path.exists(OUTPUTDIR):
        j.system.fs.createDir(OUTPUTDIR)

    for namespace in NAMESPACES:
        spacepath = os.path.join(OUTPUTDIR, namespace)
        if not os.path.exists(spacepath):
            j.system.fs.createDir(spacepath)
        for category in osiscl.listNamespaceCategories(namespace):
            categoryfile = os.path.join(spacepath, category)
            try:
                osiscl.export(namespace, category, categoryfile)
            except:
                print 'Error exporting category: %s on namespace:%s' % (category, namespace)
            
if __name__ == '__main__':
    action()