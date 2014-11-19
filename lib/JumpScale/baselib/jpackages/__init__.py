from JumpScale import j

j.base.loader.makeAvailable(j, 'packages')

from .JPackageClient import JPackageClient
j.packages=JPackageClient()

from .ReleaseMgmt import ReleaseMgmt
j.packages.releaseMgmt=ReleaseMgmt()

from .JPackagesGenDocs import JPackagesGenDocs
j.packages.docGenerator=JPackagesGenDocs()

from .PythonPackage import PythonPackage
j.base.loader.makeAvailable(j, 'system.platform')
j.system.platform.python = PythonPackage()
