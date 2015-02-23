from JumpScale import j

def cb():
    from .JobManager import JobManager
    return JobHandler()

j.base.loader.makeAvailable(j, 'core')
j.core._register('jobhandler', cb)


