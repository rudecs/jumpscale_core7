#! /usr/bin/python
from gevent import monkey
#monkey.patch_all()
monkey.patch_socket()
monkey.patch_ssl()
monkey.patch_thread()
monkey.patch_time()

from JumpScale import j
from JumpScale.baselib import cmdutils
from JumpScale.baselib.alerter.alerts_service import AlertService


if __name__ == '__main__':
    parser = cmdutils.ArgumentParser()
    parser.add_argument('-c', '--clean', default=False, action='store_true')
    opts = parser.parse_args()
    j.application.start("alerts_server")
    j.logger.consolelogCategories.append('alerter')
    j.logger.consolelogCategories.append('rogerthat')
    j.logger.consolelogCategories.append('email')
    AlertService().start(opts)
    j.application.stop()
