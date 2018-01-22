from JumpScale import j
from JumpScale.grid.osis.OSISStoreMongo import OSISStoreMongo

class mainclass(OSISStoreMongo):
    TTL = 3600 * 24 * 30 # 30 days
