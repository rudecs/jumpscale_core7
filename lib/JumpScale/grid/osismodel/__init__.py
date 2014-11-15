from JumpScale import j
import JumpScale.baselib.code
from .OSIS import OSIS
j.base.loader.makeAvailable(j, 'core')
j.core.osismodel = OSIS()
