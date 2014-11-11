import time
from JumpScale import j


if __name__ == '__main__':

    j.application.start("appserver6_client")

    client = j.core.appserver6.getAppserverClient("127.0.0.1", 9999, "1234")
    system = client.getActor("system", "master", instance=0)

    j.application.stop()
