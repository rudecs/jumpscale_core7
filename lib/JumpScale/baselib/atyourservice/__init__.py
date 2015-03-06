from JumpScale import j
from .AtYourServiceFactory import AtYourServiceFactory
from .AtYourServiceRemoteFactory import AtYourServiceRemoteFactory

j.atyourservice = AtYourServiceFactory()
j.atyourservice.remote = AtYourServiceRemoteFactory()
