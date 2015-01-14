from JumpScale import j

j.base.loader.makeAvailable(j, 'tools')
from .SSLSigning import SSLSigning
j.tools.sslSigning = SSLSigning()