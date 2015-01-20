from JumpScale import j

descr = """
backup to gitlab
"""

organization = "jumpscale"
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
category = "system.git.backup"
period = 60*60*2
enable = True
async = True
roles = ["admin"]
queue ='io'

def action():
    import JumpScale.baselib.git
    import JumpScale.baselib.motherhip1_extensions

    project = j.system.fs.joinPaths('/opt', 'code', 'git_incubaid')
    project = j.system.fs.listDirsInDir(project)[0]
    
    path =  j.system.fs.joinPaths(project, 'backup')
    gitcl = j.clients.git.getClient(project)

    j.tools.exporter.exportAll(path)

    message = '%s at %s' % (j.system.fs.getBaseName(project), j.base.time.getLocalTimeHRForFilesystem())
    gitcl.commit(message)
    gitcl.push()