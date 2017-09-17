from gevent import monkey
monkey.patch_all()

from JumpScale import j
import JumpScale.grid.osis
import time
import argparse
import sys

j.application.start("osisserver")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', help='Enable verbose logging', default=False, action='store_true')
    parser.add_argument('osisinstance', help='Choose osis instance to use', default="main")
    options = parser.parse_args()
    osishrd = j.application.getAppInstanceHRD(name="osis",instance=options.osisinstance)
    connectionsconfig = osishrd.getDictFromPrefix('instance.param.osis.connection')
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
            hrd = j.application.getAppInstanceHRD(instance=instancename, name='influxdb_client')
            database_name = hrd.getStr('instance.param.influxdb.client.dbname')
            if database_name not in databases:
                client.create_database(database_name)
            else:
                client.switch_database(database_name)
            client.query('ALTER RETENTION POLICY "default" on main DURATION 3d default')

        connections["%s_%s"%(dbname,instancename)]=client

    superadminpasswd = osishrd.get("instance.param.osis.superadmin.passwd")

    j.core.osis.startDaemon(path="", overwriteHRD=False, overwriteImplementation=False, key="", port=5544, superadminpasswd=superadminpasswd, dbconnections=connections, hrd=osishrd, verbose=options.verbose)

    j.application.stop()
