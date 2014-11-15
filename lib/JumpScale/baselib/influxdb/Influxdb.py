from JumpScale import j
import redis
from influxdb import client as influxdb

class InfluxdbFactory:

    """
    """

    def __init__(self):
        pass

    def get(self, host='localhost', port=8086,username='root', password='root', database=None, ssl=False, verify_ssl=False, timeout=None, use_udp=False, udp_port=4444):
        db = influxdb.InfluxDBClient(host=host, port=port,username=username, password=password, database=database, ssl=ssl, \
            verify_ssl=verify_ssl, timeout=timeout, use_udp=use_udp, udp_port=udp_port)
        return db

