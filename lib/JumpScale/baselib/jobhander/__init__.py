from JumpScale import j

from .JobManager import JobManager

j.base.loader.makeAvailable(j, 'core')

j.core.jobhandler=JobHandler()


