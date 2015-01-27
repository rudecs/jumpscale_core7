from JumpScale import j
from .JPackageFactory import JPackageFactory
from .JPackageRemote import JPackageRemoteFactory

j.packages = JPackageFactory()
j.packages.remote = JPackageRemoteFactory()
