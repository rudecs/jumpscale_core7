from JumpScale import j

import JumpScale.grid.zdaemon

from .ZDaemonClient import ZDaemonCmdClient
import JumpScale.grid.socketserver

j.logger.consoleloglevel = 5


class ZDaemonAgent(ZDaemonCmdClient):

    def __init__(self, ipaddr="127.0.0.1", port=5650, org="myorg", user="root", passwd="1234", ssl=False, reset=False, roles=[]):
        ZDaemonCmdClient.__init__(self, ipaddr=ipaddr, port=port, user=user, passwd=passwd, ssl=ssl, reset=reset, roles=roles)

    def start(self):
        ##TODO
        pass
