import os
import re
import dns.zone
from dns.zone import NoSOA
from dns.name import Name
import dns.rdatatype
from dns.rdtypes.IN.A import A
from base import DNS
from JumpScale import j

j.logger.enabled = True

class Zone(object):
    CONFIG_FILES_DIR = '/etc/bind/'
    NON_ZONE_FILES = ['/etc/bind/named.conf.options']

    def __init__(self, domain, type, file):
        self.domain = domain
        self.type = type
        self.file = file
    
    def __repr__(self):
        return "{domain:%s, type:%s, file:%s}" % (self.domain, self.type, self.file)
    
    @staticmethod
    def getZones():
        j.logger.log('GETTING ZONES INFO', 2)
        configs = []
        zonesfiles = []
        for configfile in ['named.conf.local', 'named.conf']:
            configs.append(''.join(os.path.join(Zone.CONFIG_FILES_DIR, configfile)))

        for file in configs:
            with open(file) as f:
                for line in re.findall('^include \".*\";$', f.read(), re.M):
                    path = line.replace('include ', '').replace('"', '').replace(';', '')
                    if path not in Zone.NON_ZONE_FILES:
                        zonesfiles.append(path)
        zones = {}
        for file in zonesfiles:
            with open(file) as f:
                for match in re.finditer('zone \"(?P<domain>.*)\" \{(?P<data>[^\}]+)', f.read()):
                    domain = match.group('domain')
                    data = match.group('data')
                    domaindata = dict()
                    for fieldm in re.finditer("^\s+(?P<key>\w+)\s+(?P<value>.*);$", data, re.M):
                        domaindata[fieldm.group('key')] = fieldm.group('value') 
                    if not domaindata:
                        continue
                    zones[domain] = domaindata
                    zones[domain]['file'] = zones[domain]['file'].replace('"', '')
        return zones
    
    @staticmethod
    def getMap(zones):
        res = {}
        for k, v in Zone.getZones().iteritems():
            try:
                zone = dns.zone.from_file(v['file'], os.path.basename(v['file']), relativize=False)
                for (name, ttl, rdata) in zone.iterate_rdatas('A'):
                    key = name.to_text().rstrip('.')
                    val = res.get(key, [])
                    if not {'ip':rdata.address, 'file':v['file']} in val:
                        val.append({'ip':rdata.address, 'file':v['file']})
                    res[key] = val
            except NoSOA:
                continue
        return res

    @staticmethod
    def getreverseMap(zones):
        res = {}
        for k, v in Zone.getZones().iteritems():
            try:
                zone = dns.zone.from_file(v['file'], os.path.basename(v['file']), relativize=False)
                for (name, ttl, rdata) in zone.iterate_rdatas('A'):
                    value = res.get(rdata.address, [])
                    value.append({ 'file':v['file'], 'domain':name.to_text().rstrip('.')})
                    res[rdata.address] = value
            except NoSOA:
                continue
        return res
    
class BindDNS(DNS):

    @property
    def zones(self):
        res = []
        for k, v in Zone.getZones().iteritems():
            z = Zone(k, v['type'], v['file'])
            res.append(z)
        return res
    
    @property
    def map(self):
        return Zone.getMap(self.zones)

    @property
    def reversemap(self):
        return Zone.getreverseMap(self.zones)

    def start(self):
        j.logger.log('STARTING BIND SERVICE', 2)
        _, out = j.system.process.execute('service bind9 start', outputToStdout=True)
        j.logger.log(out, 2)
        
    def stop(self):
        j.logger.log('STOPPING BIND SERVICE', 2)
        _, out = j.system.process.execute('service bind9 stop', outputToStdout=True)
        j.logger.log(out, 2)
    
    def restart(self):
        j.logger.log('RESTSRTING BIND SERVICE', 2)
        _, out = j.system.process.execute('service bind9 restart', outputToStdout=True)
        j.logger.log(out, 2)

    def updateHostIp(self, host, ip):
        map = self.map
        record = map.get(host)
        if not record:
            raise RuntimeError("Invalid host name")

        for r in record:
            file = r['file']
            old_ip = r['ip']
            zone = dns.zone.from_file(file, os.path.basename(file),relativize=False)
            for k, v in zone.iteritems():
                for dataset in v.rdatasets:
                    for item in dataset.items:
                        if hasattr(item, 'address') and item.address == old_ip:
                            item.address = ip
                            zone.to_file(file)
        self.restart()

    def addRecord(self, domain, host, ip, klass, type, ttl):
        host = "%s." % host
        records  = [x for x in self.zones if x.domain == domain]
        if not records:
            raise RuntimeError("Invalid domain")
        
        record = records[0]
        file = record.file
        zone = dns.zone.from_file(file, os.path.basename(file),relativize=False)
        node = zone.get_node(host, create=True)
        
        if type == "A":
            t = dns.rdatatype.A
        
        if klass == "IN":
            k = dns.rdataclass.IN

        ds = node.get_rdataset(t, k, covers=dns.rdatatype.NONE, create=True)
        ds.ttl = ttl
        if type == "A" and klass == "IN":
            item = A(k, t, ip)
            ds.items.append(item)
        
        # update version
        for k, v in zone.nodes.iteritems():
            for ds in v.rdatasets:
                if ds.rdtype == dns.rdatatype.SOA:
                    for item in ds.items:
                        item.serial += 1
        
        zone.to_file(file, relativize=False)
        self.restart()

    def deleteHost(self, host):
        host = host.rstrip('.')
        map = self.map
        record = map.get(host)
        if not record:
            raise RuntimeError("Invalid host name")
        
        for r in record:
            file = r['file']
            old_ip = r['ip']
            zone = dns.zone.from_file(file, os.path.basename(file),relativize=False)
            for k, v in zone.nodes.copy().iteritems():
                if k.to_text() == "%s." % host:
                    zone.delete_node(k)
            # update version
            for k, v in zone.nodes.iteritems():
                for ds in v.rdatasets:
                    if ds.rdtype == dns.rdatatype.SOA:
                        for item in ds.items:
                            item.serial += 1
            
            zone.to_file(file, relativize=False)
        self.restart()