from JumpScale import j
from JumpScale.grid.osis.OSISStore import OSISStore

ujson = j.db.serializers.getSerializerType('j')

class mainclass(OSISStore):

    def __init__(self, dbconnections):
        self.elasticsearch = None
        if 'influxdb_main' in dbconnections:
            self.dbclient = dbconnections['influxdb_main']
        else:
            self.dbclient=None

    def set(self, key, value, waitIndex=False, session=None):
        stats = value
        series = list()
        for key, stats in value.items():
            data = {'name': key, 'points': []}
            for stat in stats:
                if 'columns' not in data:
                    data['columns'] = list(stat.keys())
                data['points'].append(list(stat.values()))
            series.append(data)
        self.dbclient.write_points(series)

    def delete(self, key, session=None):
        seriesName = key
        self.dbclient.delete_series(seriesName)

    def find(self, query, start=0, size =100, session=None):
        return self.dbclient.query(query).raw

    def destroyindex(self, session=None):
        raise RuntimeError("osis 'destroyindex' for stat not implemented")

    def getIndexName(self):
        return "system_stats"

    def get(self,key, session=None):
        raise RuntimeError("osis 'get' for stat not implemented")

    def exists(self,key, session=None):
        raise RuntimeError("osis exists for stat not implemented")
        #work with elastic search only


    #NOT IMPLEMENTED METHODS WHICH WILL NEVER HAVE TO BE IMPLEMENTED

    def setObjIds(self,**args):
        raise RuntimeError("osis method setObjIds is not relevant for stats namespace")

    def rebuildindex(self,**args):
        raise RuntimeError("osis method rebuildindex is not relevant for stats namespace")

    def list(self,**args):
        raise RuntimeError("osis method list is not relevant for stats namespace")

    def removeFromIndex(self,**args):
        raise RuntimeError("osis method removeFromIndex is not relevant for stats namespace")

