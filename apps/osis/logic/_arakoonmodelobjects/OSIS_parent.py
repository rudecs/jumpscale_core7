from JumpScale import j
class mainclass(j.core.osis.getOsisImplementationParentClass("_modelobjects")):
    """
    Defeault object implementation
    """

    def _getDB(self):
        return j.db.keyvaluestore.getArakoonStore('osis')
