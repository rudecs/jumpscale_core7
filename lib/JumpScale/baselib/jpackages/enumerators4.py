from JumpScale.core.baseclasses import BaseEnumeration

class DependencyType4(BaseEnumeration):
    """
    One of two constants: runtime and build.
    When a package has a runtime dependency on another package it means the first package cannot operate properly without the second package being installed.
    When a package has a build dependency on another package it means the first package cannot be build without the second package being installed.
    The second package typically is some build tool like gcc.
    #@todo doc
    """
    pass

DependencyType4.registerItem('runtime')
DependencyType4.registerItem('build')
DependencyType4.registerItem('native')
DependencyType4.registerItem('python')
DependencyType4.finishItemRegistration()


class VListType4(BaseEnumeration):
    """
    #@todo doc
    """
    pass

VListType4.registerItem('server')
VListType4.registerItem('client')
VListType4.finishItemRegistration()


class ACLPermission4(BaseEnumeration):
    """
    #@todo doc
    """
    pass
ACLPermission4.registerItem('R')

ACLPermission4.registerItem('W') ##only write access? for rsync that is not possible, no?
ACLPermission4.registerItem('RW')
ACLPermission4.finishItemRegistration()


class JPackageState4(BaseEnumeration):
    """
    The states a JPackage can find itself in.
    """
    pass

JPackageState4.registerItem('ERROR')
JPackageState4.registerItem('OK')
JPackageState4.finishItemRegistration()

class JPackageQualityLevelType4(BaseEnumeration):
    """ JPackage quality level """
    def __repr__(self):
        return str(self)
        
JPackageQualityLevelType4.registerItem('trunk')
JPackageQualityLevelType4.registerItem('test')
JPackageQualityLevelType4.registerItem('stable')
JPackageQualityLevelType4.registerItem('beta')
JPackageQualityLevelType4.registerItem('unstable')
JPackageQualityLevelType4.finishItemRegistration()