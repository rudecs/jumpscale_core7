from JumpScale import j

# import sys
import time
import json
# import os
import psutil


class InfluxDumper():

    def __init__(self,redis,server="localhost",port=8086,login="root",passwd="root",dbname="monitoring"):
        self.redis=redis
        self.dbname=dbname
        self.influxdb=j.clients.influxdb.get(host=server, port=port, username=login, password=passwd, database=None, ssl=False, verify_ssl=False, timeout=None, use_udp=False, udp_port=4444)
        
        # dbs=self.influxdb.get_list_database()
        # if "stats" not in [item["name"] for item in dbs]:
        #     self.influxdb.create_database("stats")
        try:
            self.influxdb.drop_database(self.dbname)
        except:
            pass
        self.influxdb.create_database(self.dbname)
        self.influxdb.switch_database('monitoring')

    def start(self):
        q='queues:stats'
        while True:
            res=self.redis.lpop(q)
            counter=+1
            start=time.time()
            data=[]
            while res!=None:
                measurement,key,tags,epoch,last,mavg,mmax,havg,hmax=res.split("|")
                # points.append(self.getPoint(key,timestamp=epoch,tags=None,last=last+"i",min_avg=mavg+"i",min_max=mmax+"i",h_avg=havg+"i",h_max=hmax+"i"))
                tagslist = tags.split(',') # [node:2, d:3]
                
                tags = {x.split(":")[0]:x.split(":")[1] for x  in tagslist }
                
                data.append({
                        "measurement": measurement,
                        "tags": tags,
                        "time": j.base.time.epoch2HRDateTime(epoch),
                        "fields": {
                            "value": last
                        }
                    })
                                
                if counter>100 or time.time()>start+2:
                    start=time.time()
                    counter=0
                    # print data
                    self.influxdb.write_points(data)
                    # self.influxdb.write_points(points, time_precision="s", database="main", retention_policy=None, tags=None, batch_size=None)
                    data=[]
                counter+=1
                res=self.redis.lpop(q)
                print res
            time.sleep(1)            
