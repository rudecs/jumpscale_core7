from JumpScale import j

def ssh2():
    from .SSHTool import SSHTool
    return SSHTool()

j.base.loader.makeAvailable(j, 'remote')
j.remote._register('ssh', ssh2)
