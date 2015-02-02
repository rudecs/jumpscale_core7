from JumpScale import j
import JumpScale.grid.osis
import time

j.application.start("osisserver")

import sys
if __name__ == '__main__':

    args=sys.argv
    osis_instance=args[1]
    osishrd = j.application.getAppInstanceHRD(name="osis",instance=osis_instance)
    connectionsconfig = osishrd.getDictFromPrefix('param.osis.connection')
    connections = {}

    for dbname, instancename in connectionsconfig.items():
        print("connect to: %s"%dbname)

        if dbname=="mongodb":
            import JumpScale.grid.mongodbclient
            client=j.clients.mongodb.getByInstance(instancename)

        elif dbname=="redis":
            import JumpScale.baselib.redis
            while not j.clients.redis.isRunning(instancename):
                time.sleep(0.1)
                print("cannot connect to redis, will keep on trying forever, please start (%s)"%(instancename))
            client=j.clients.redis.getByInstance(instancename)

        elif dbname=="influxdb":
            import JumpScale.baselib.influxdb
            client = j.clients.influxdb.getByInstance(instancename)
            databases = [db['name'] for db in client.get_list_database()]
            if 'main' not in databases:
                client.create_database('main')
            else:
                client.switch_database('main')

        connections["%s_%s"%(dbname,instancename)]=client

    superadminpasswd = osishrd.get("param.osis.superadmin.passwd")

    j.core.osis.startDaemon(path="", overwriteHRD=False, overwriteImplementation=False, key="", port=5544, superadminpasswd=superadminpasswd, dbconnections=connections, hrd=osishrd)

    j.application.stop()
