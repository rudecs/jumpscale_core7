from JumpScale import j

location = "Lenoir1"
data = {}
data["instance.name"] = location
data["instance.description"] = "Our %s location." % location
location = j.atyourservice.new(name="location", instance=location.lower(), args=data)
location.init()


data = {}
data['instance.key.priv'] = ''  # empty private key trigger auto generation
# notice here how we specifiy the relation between the location and the sshkey service,
# just add the 'parent=' parameter to the service creation and the sshkey will be a child service of the location.
keyInstance = j.atyourservice.new(name='sshkey', instance="mykey", args=data, parent=location)
keyInstance.init()
keyInstance.install()


machines = [
            {'ip': '185.69.164.120',
            'port': 2223,
            'name': 'gr1',
            'login': 'cloudscalers',
            'password': 'ifwzuD6dA'
            },
            {'ip': '185.69.164.120',
            'port': 2224,
            'name': 'gr2',
            'login': 'cloudscalers',
            'password': 'HUlsP91wH'
            },
            {'ip': '185.69.164.120',
            'port': 2225,
            'name': 'gr3',
            'login': 'cloudscalers',
            'password': 'NXh35E5eO'
            },
        ]
nodes = {}
for machine in machines:
    data = {}
    data["ip"] = machine['ip']
    data["ssh.port"] = machine['port']
    data['sshkey'] = keyInstance.instance
    data['login'] = machine['login']
    data['password'] = machine['password']
    node = j.atyourservice.new(name='node.ssh', args=data, instance=machine['name'], parent=location)
    node.init()
    node.install()
    nodes[machine['name']] = node

# deploy 3 mongo
for x in range(3):
    node = nodes.values()[x]
    data = {}
    data['param.name'] = 'mongodb_%s' % x
    data['param.image'] = 'despiegk/mc'
    data['param.portsforwards'] = '27017:27017 28017:28017'
    data['param.volumes'] = '/opt/jumpscale7/var/mongodb:/opt/jumpscale7/var/mongodb'
    mongodocker = j.atyourservice.new(name='node.docker', args=data, instance=data['param.name'], parent=node)
    mongodocker.consume('node', node.instance)
    mongodocker.init()
    mongodocker.install()

    mdata = {}
    mdata['param.host'] = '127.0.0.1'
    mdata['param.port'] = 27017
    mdata['param.replicaset'] = 'ays'
    mongo = j.atyourservice.new(name='mongodb', args=mdata, instance=mongodocker.instance, parent=mongodocker)
    mongodocker.consume('node', mongodocker.instance)
    mongodocker.init()
    mongodocker.install()


print node
