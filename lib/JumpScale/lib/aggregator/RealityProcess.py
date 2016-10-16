from InfluxDumper import InfluxDumper

class RealityProcess:
    """
    """

    def __init__(self):
        pass

    def influxpump(self, influxdb, cidr='127.0.0.1', ports=[7777], workers=4):
        """
        will dump redis stats into influxdb(s)
        get connections from jumpscale clients...
        """

        InfluxDumper(influxdb, cidr=cidr, ports=ports).start(workers=workers)
