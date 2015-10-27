import requests
import time
from JumpScale import j
import JumpScale.portal
# import JumpScale.lib.cloudrobots

import JumpScale.baselib.remote
# import JumpScale.baselib.redis
import JumpScale.portal
import ujson as json
import sys

class Output(object):
    def __init__(self):
        self.out=""
        self.lastlines=""
        self.counter=0

    def _write(self):
        self.lastlines=self.lastlines.replace("\n\n","\n")
        self.lastlines=self.lastlines.replace("\n\n","\n")
        self.lastlines=self.lastlines.replace("\n\n","\n")
        self.ms1.action.sendUserMessage(self.lastlines)
        self.lastlines=""
        self.counter=0

    def write(self, buf,**args):
        if self.lastlines.find(buf)==-1:
            self.lastlines+="%s\n"%buf
            if self.counter>20:
                self._write()
            if len(self.lastlines.split("\n"))>20:
                self._write()
            self.counter+=1

    def isatty(self):
        return False

    def flush(self):
        return None


class MS1Factory(object):
    def get(self, apiURL='www.mothership1.com'):
        return MS1(apiURL)


class MS1(object):

    def __init__(self, apiURL):
        self.apiURL = apiURL
        self.secret = ''
        self.IMAGE_NAME = 'Ubuntu 14.04'
        # self.redis_cl = j.clients.redis.getByInstance('system')
        self.stdout=Output()
        self.stdout.ms1=self
        self.stdout.prevout=sys.stdout
        self.action=None
        self.vars={}
        self.db=j.db.keyvaluestore.getFileSystemStore("/tmp/ms1.db")


    def getCloudspaceObj(self, space_secret,**args):
        if not self.db.exists('cloudrobot:cloudspaces:secrets', space_secret):
            raise RuntimeError("E:Space secret does not exist, cannot continue (END)")
        space=json.loads(self.db.get('cloudrobot:cloudspaces:secrets', space_secret))
        return space

    def getCloudspaceId(self, space_secret):
        space=self.getCloudspaceObj(space_secret)
        return space["id"]

    def getCloudspaceSecret(self, login, password, cloudspace_name, location='default', spacesecret=None,**args):
        """
        @param location ca1 (canada),us2 (us)
        """
        params = {'username': login, 'password': password}
        response = requests.post('https://%s/restmachine/cloudapi/users/authenticate' % self.apiURL, params)
        if response.status_code != 200:
            raise RuntimeError("E:Could not authenticate user %s" % login)
        auth_key = response.json()
        params = {'authkey': auth_key}
        response = requests.post('https://%s/restmachine/cloudapi/cloudspaces/list' % self.apiURL, params)
        cloudspaces = response.json()

        cloudspace = [cs for cs in cloudspaces if cs['name'] == cloudspace_name and cs['location'] == location]
        if cloudspace:
            cloudspace = cloudspace[0]
        else:
            raise RuntimeError("E:Could not find a matching cloud space with name %s and location %s" % (cloudspace_name, location))

        self.db.set('cloudrobot:cloudspaces:secrets', auth_key, json.dumps(cloudspace))

        return auth_key

    def sendUserMessage(self,msg,level=2,html=False,args={}):
        if self.action!=None:
            self.action.sendUserMessage(msg,html=html)
        else:
            print(msg)

    def getApiConnection(self, space_secret,**args):
        host = self.apiURL # if cs["location"] == 'ca1' else '%s.mothership1.com' % cs["location"]
        try:
            api=j.clients.portal.get(host, 443, space_secret)
        except Exception as e:
            raise RuntimeError("E:Could not login to MS1 API.")

        return api

    # def deployAppDeck(self, spacesecret, name, memsize=1024, ssdsize=40, vsansize=0, aysdomain='solutions', aysname=None, config=None, description=None,**args):
    #     machine_id = self.deployMachineDeck(spacesecret, name, memsize, ssdsize, vsansize, description)
    #     api = self.getApiConnection(location)
    #     portforwarding_actor = api.getActor('cloudapi', 'portforwarding')
    #     cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
    #     machines_actor = api.getActor('cloudapi', 'machines')
    #     # create ssh port-forward rule
    #     for _ in range(30):
    #         machine = machines_actor.get(machine_id)
    #         if j.basetype.ipaddress.check(machine['interfaces'][0]['ipAddress']):
    #             break
    #         else:
    #             time.sleep(2)
    #     if not j.basetype.ipaddress.check(machine['interfaces'][0]['ipAddress']):
    #         raise RuntimeError('Machine was created, but never got an IP address')
    #     cloudspace_forward_rules = portforwarding_actor.list(machine['cloudspaceid'])
    #     public_ports = [rule['publicPort'] for rule in cloudspace_forward_rules]
    #     ssh_port = '2222'
    #     cloudspace = cloudspaces_actor.get(machine['cloudspaceid'])
    #     while True:
    #         if ssh_port not in public_ports:
    #             portforwarding_actor.create(machine['cloudspaceid'], cloudspace['publicipaddress'], ssh_port, machine['id'], '22')
    #             break
    #         else:
    #             ssh_port = str(int(ssh_port) + 1)

    #     # do an ssh connection to the machine
    #     if not j.system.net.waitConnectionTest(cloudspace['publicipaddress'], int(ssh_port), 60):
    #         raise RuntimeError("Failed to connect to %s %s" % (cloudspace['publicipaddress'], ssh_port))
    #     ssh_connection = j.remote.cuisine.api
    #     username, password = machine['accounts'][0]['login'], machine['accounts'][0]['password']
    #     ssh_connection.fabric.api.env['password'] = password
    #     ssh_connection.fabric.api.env['connection_attempts'] = 5
    #     ssh_connection.connect('%s:%s' % (cloudspace['publicipaddress'], ssh_port), username)

    #     # install ays there
    #     ssh_connection.sudo('ays mdupdate')
    #     if config:
    #         ays_hrd_file = j.system.fs.joinPaths(j.dirs.hrdDir, '%s_%s' % (aysdomain, aysname))
    #         ssh_connection.file_write(ays_hrd_file, config, sudo=True)
    #     if aysdomain and aysname:
    #         ssh_connection.sudo('ays install -n %s -d %s' % (aysname, aysdomain))

    #     #cleanup
    #     cloudspace_forward_rules = portforwarding_actor.list(machine['cloudspaceid'])
    #     ssh_rule_id = [rule['id'] for rule in cloudspace_forward_rules if rule['publicPort'] == ssh_port][0]
    #     portforwarding_actor.delete(machine['cloudspaceid'], ssh_rule_id)
    #     if config:
    #         hrd = j.core.hrd.get(content=config)
    #         if hrd.exists('services_ports'):
    #             ports = hrd.getList('services_ports')
    #             for port in ports:
    #                 portforwarding_actor.create(machine['cloudspaceid'], cloudspace['publicipaddress'], str(port), machine['id'], str(port))
    #     return {'publicip': cloudspace['publicipaddress']}

    def getMachineSizes(self,spacesecret, cloudspaceId):
        if self.db.exists("ms1", "ms1:cache:%s:sizes"%spacesecret):
            return json.loads(self.db.get('ms1', "ms1:cache:%s:sizes"%spacesecret))
        api = self.getApiConnection(spacesecret)
        sizes_actor = api.getActor('cloudapi', 'sizes')
        try:
            sizes=sizes_actor.list(cloudspaceId=cloudspaceId)
        except TypeError:
            sizes=sizes_actor.list()
        self.db.set("ms1", "ms1:cache:%s:sizes"%spacesecret,json.dumps(sizes))
        return sizes

    def createMachine(self, spacesecret, name, memsize=1, ssdsize=40, vsansize=0, description='',
                      imagename="ubuntu.14.04.x64",delete=False, sshkey=None, hostname="", stackId=None, disks=None,**args):
        """
        memsize  #size is 0.5,1,2,4,8,16 in GB
        ssdsize  #10,20,30,40,100 in GB
        imagename= fedora,windows,ubuntu.13.10,ubuntu.12.04,windows.essentials,ubuntu.14.04.x64
                   zentyal,debian.7,arch,fedora,centos,opensuse,gitlab,ubuntu.jumpscale

        sshkey = is content of pub key or path
        hostname if "" then will be same as name
        stack stackId where to create the vm. if not None
              the vm will be created on this stack. otherwise best stack will be choosen automaticly
        """
        if delete:
            self.deleteMachine(spacesecret, name)

        self.vars = {}

        if sshkey!="":
            if j.system.fs.exists(path=sshkey):
                if sshkey.find(".pub")==-1:
                    j.events.inputerror_critical("public key path needs to have .pub at the end.")
                sshkey=j.system.fs.fileGetContents(sshkey)

        ssdsize = int(ssdsize)
        try:
            memsize = int(memsize)
        except:
            # support for 0.5 memsize
            memsize = float(memsize)
        ssdsizes = {}
        ssdsizes[10] = 10
        ssdsizes[20] = 20
        ssdsizes[30] = 30
        ssdsizes[40] = 40
        ssdsizes[100] = 100
        memsizes = {}
        memsizes[0.5] = 512
        memsizes[1] = 1024
        memsizes[2] = 2048
        memsizes[4] = 4096
        memsizes[8] = 8192
        memsizes[16] = 16384
        if memsize not in memsizes:
            raise RuntimeError("E: supported memory sizes are 0.5,1,2,4,8,16 (is in GB), you specified:%s"%memsize)
        if ssdsize not in ssdsizes:
            raise RuntimeError("E: supported ssd sizes are 10,20,30,40,100  (is in GB), you specified:%s"%memsize)

        # get actors
        api = self.getApiConnection(spacesecret)
        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
        machines_actor = api.getActor('cloudapi', 'machines')
        if stackId is not None:
            machine_cb_actor = api.getActor('cloudbroker', 'machine')
        cloudspace_id = self.getCloudspaceId(spacesecret)

        self.vars["cloudspace.id"] = cloudspace_id
        self.vars["machine.name"] = name

        memsize2 = memsizes[memsize]
        size_ids = [size['id'] for size in self.getMachineSizes(spacesecret, cloudspace_id) if size['memory'] == int(memsize2)]
        if len(size_ids)==0:
            raise RuntimeError('E:Could not find a matching memory size %s'% memsize2)

        ssdsize2=ssdsizes[ssdsize]

        images=self.listImages(spacesecret)

        if not imagename in list(images.keys()):
            j.events.inputerror_critical("Imagename '%s' not in available images: '%s'"%(imagename,images))

        templateid=images[imagename][0]

        self.sendUserMessage("create machine: %s"%(name))

        if stackId and machine_cb_actor:
            # we want to deploy on a specific stack
            def valid():
                machines = machine_cb_actor.list(cloudspaceId=cloudspace_id)
                names = []
                for m in machines:
                    if m['status'] != 'DESTROYED':
                        names.append(m['name'])
                if name in names:
                    j.events.inputerror_critical("Could not create machine it does already exist.","ms1.createmachine.exists")

                    return False
                cloudspaceObj = cloudspaces_actor.get(cloudspace_id)
                if cloudspaceObj['status'] not in ['DEPLOYED', 'VIRTUAL']:
                    j.events.inputerror_critical("Could not create machine it does already exist.","ms1.createmachine.exists")
                    return False
                return True

            if valid():
                try:
                    machine_id = machine_cb_actor.createOnStack(cloudspaceId=cloudspace_id, name=name, description=description, sizeId=size_ids[0], imageId=templateid, disksize=int(ssdsize2), stackid=stackId, datadisks=disks)
                except Exception as e:
                    j.events.opserror_critical("Could not create machine on stack %s, unknown error : %s." % (stackId, e.message), "ms1.createmachine.exists")
        else:
            try:
                if disks == None:
                    machine_id = machines_actor.create(cloudspaceId=cloudspace_id, name=name, description=description, \
                        sizeId=size_ids[0], imageId=templateid, disksize=int(ssdsize2))
                else:
                    machine_id = machines_actor.create(cloudspaceId=cloudspace_id, name=name, description=description, \
                        sizeId=size_ids[0], imageId=templateid, disksize=int(ssdsize2), datadisks=disks)

            except Exception as e:
                if str(e).find("Selected name already exists") != -1:
                   j.events.inputerror_critical("Could not create machine it does already exist.","ms1.createmachine.exists")
                raise RuntimeError("E:Could not create machine, unknown error : %s", e.message)

        self.vars["machine.id"] = machine_id

        self.sendUserMessage("machine created")
        self.sendUserMessage("find free ipaddr & tcp port")

        for _ in range(60):
            machine = machines_actor.get(machine_id)
            if j.basetype.ipaddress.check(machine['interfaces'][0]['ipAddress']):
                break
            else:
                time.sleep(1)
        if not j.basetype.ipaddress.check(machine['interfaces'][0]['ipAddress']):
            raise RuntimeError('E:Machine was created, but never got an IP address')

        self.vars["machine.ip.addr"] = machine['interfaces'][0]['ipAddress']

        # push initial key
        self.sendUserMessage("push initial ssh key")
        ssh = self._getSSHConnection(spacesecret, name, sshkey=sshkey, **args)

        self.sendUserMessage("machine active & reachable")

        self.sendUserMessage("to connect from outise cloudspace do: 'ssh %s -p %s'" % (self.vars["space.ip.pub"], self.vars["machine.last.tcp.port"]))
        self.sendUserMessage("to connect from inside cloudspace do: 'ssh %s -p %s'" % (self.vars["machine.ip.addr"], 22))

        ss = ssh.host().split(':')
        return machine_id, ss[0], (ss[1] if ss[1] else 22)

    def getMachineObject(self,spacesecret, name,**args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        machine = machines_actor.get(machine_id)
        return machine

    def listImages(self,spacesecret,**args):

        if self.db.exists("ms1", "ms1:cache:%s:images"%spacesecret):
            return json.loads(self.db.get('ms1', "ms1:cache:%s:images"%spacesecret))

        api = self.getApiConnection(spacesecret)
        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
        images_actor = api.getActor('cloudapi', 'images')
        result={}
        alias={}
        imagetypes=["ubuntu.jumpscale","fedora","windows","ubuntu.13.10","ubuntu.12.04","windows.essentials","ubuntu.14.04.x64","ubuntu 14.04 x64",\
            "zentyal","debian.7","arch","fedora","centos","opensuse","gitlab"]
        for image in images_actor.list():
            name=image["name"]
            namelower=name.lower()
            for imagetype in imagetypes:
                if namelower.find(imagetype) != -1:
                    result[imagetype]=[image["id"],image["name"]]
            result[image['name']]=[image["id"],image["name"]]

        self.db.set("ms1", "ms1:cache:%s:images"%spacesecret,json.dumps(result))
        return result

    def listMachinesInSpace(self, spacesecret,**args):
        # get actors
        api = self.getApiConnection(spacesecret)
        machines_actor = api.getActor('cloudapi', 'machines')
        cloudspace_id = self.getCloudspaceId(spacesecret)
        # list machines
        machines = machines_actor.list(cloudspaceId=cloudspace_id)
        return machines

    def _getMachineApiActorId(self, spacesecret, name,**args):
        api=self.getApiConnection(spacesecret)
        cloudspace_id = self.getCloudspaceId(spacesecret)
        machines_actor = api.getActor('cloudapi', 'machines')
        machine_id = [machine['id'] for machine in machines_actor.list(cloudspace_id) if machine['name'] == name]
        if len(machine_id)==0:
            raise RuntimeError("E:Could not find machine with name:%s, cannot continue action."%name)
        machine_id = machine_id[0]
        actor=api.getActor('cloudapi', 'machines')
        return (api,actor,machine_id,cloudspace_id)

    def deleteMachine(self, spacesecret, name,**args):
        self.sendUserMessage("delete machine: %s"%(name))
        try:
            api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        except Exception as e:
            if str(e).find("Could not find machine")!=-1:
                return "NOTEXIST"
            if str(e).find("Space secret does not exist")!=-1:
                return "E:SPACE SECRET IS NOT CORRECT"
            raise RuntimeError(e)
        try:
            machines_actor.delete(machine_id)
        except Exception as e:
            print(e)
            raise RuntimeError("E:could not delete machine %s"%name)
        return "OK"

    def startMachine(self, spacesecret, name,**args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        try:
            machines_actor.start(machine_id)
        except Exception as e:
            raise RuntimeError("E:could not start machine.")
        return "OK"

    def stopMachine(self, spacesecret, name,**args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        try:
            machines_actor.stop(machine_id)
        except Exception as e:
            raise RuntimeError("E:could not stop machine.")
        return "OK"

    def snapshotMachine(self, spacesecret, name, snapshotname,**args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        try:
            machines_actor.snapshot(machine_id,snapshotname)
        except Exception as e:
            raise RuntimeError("E:could not stop machine.")
        return "OK"

    def createTcpPortForwardRule(self, spacesecret, name, machinetcpport, pubip="", pubipport=22,**args):
        self.vars["machine.last.tcp.port"]=pubipport
        return self._createPortForwardRule(spacesecret, name, machinetcpport, pubip, pubipport, 'tcp')

    def createUdpPortForwardRule(self, spacesecret, name, machineudpport, pubip="", pubipport=22,**args):
        return self._createPortForwardRule(spacesecret, name, machineudpport, pubip, pubipport, 'udp')

    def deleteTcpPortForwardRule(self, spacesecret, name, machinetcpport, pubip='', pubipport=22,**args):
        return self._deletePortForwardRule(spacesecret, name, pubip, pubipport, 'tcp')

    def deleteUdpPortForwardRule(self, spacesecret, name, machinetcpport, pubip='', pubipport=22,**args):
        return self._deletePortForwardRule(spacesecret, name, pubip, pubipport, 'udp')

    def _createPortForwardRule(self, spacesecret, name, machineport, pubip, pubipport, protocol):
        # self.sendUserMessage("Create PFW rule:%s %s %s"%(pubip,pubipport,protocol),args=args)
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        portforwarding_actor = api.getActor('cloudapi', 'portforwarding')
        if pubip=="":
            cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
            cloudspace = cloudspaces_actor.get(cloudspace_id)
            pubip=cloudspace['publicipaddress']

        self.vars["space.ip.pub"]=pubip
        self._deletePortForwardRule(spacesecret, name, pubip, pubipport, 'tcp')
        portforwarding_actor.create(cloudspace_id, pubip, str(pubipport), machine_id, str(machineport), protocol)

        return "OK"

    def addDisk(self, spaceSecret, vmName, diskName, size=10, description=None, type='D'):
        """
        Add a disk to a vm
        @param spaceSecret str: cloudspace secret
        @param vmName str: name of the vm
        @param diskName str: name of the disk
        @param size int: size of the disk in GB, min 1, max 2000
        @param description str: description of the disk
        @param type str: type of the disk B=Boot;D=Data;T=Temp
        """
        types = ['B', 'D', 'T']
        if type not in types:
            j.events.inputerror_critical('type should be one of these : %s' ', '.join(types))

        if int(size) > 2000:
            j.events.inputerror_critical('max size is 2000 GB')
        if int(size) < 1:
            j.events.inputerror_critical('min size is 1 GB')

        api, machines_actor, machine_id, cloudspace_id = self._getMachineApiActorId(spaceSecret, vmName)

        vmStatus = machines_actor.get(machine_id)
        if vmStatus['status'] != 'HALTED':
            j.events.opserror_critical('The VM should be alted to add a disk', category='')

        self.sendUserMessage('creation of the disk %s (%s GB)' % (diskName, size))
        machines_actor.addDisk(machineId=machine_id, diskName=diskName, description=description, size=size, type=type)

    def _deletePortForwardRule(self, spacesecret, name,pubip,pubipport, protocol):
        # self.sendUserMessage("Delete PFW rule:%s %s %s"%(pubip,pubipport,protocol),args=args)
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        portforwarding_actor = api.getActor('cloudapi', 'portforwarding')
        if pubip=="":
            cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
            cloudspace = cloudspaces_actor.get(cloudspace_id)
            pubip=cloudspace['publicipaddress']

        for item in portforwarding_actor.list(cloudspace_id):
            if int(item["publicPort"])==int(pubipport) and item['publicIp']==pubip:
                print(("delete portforward: %s "%item["id"]))
                portforwarding_actor.delete(cloudspace_id,item["id"])

        return "OK"

    def getFreeIpPort(self,spacesecret,mmin=90,mmax=1000,**args):
        api=self.getApiConnection(spacesecret)
        cloudspace_id = self.getCloudspaceId(spacesecret)
        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')

        space=cloudspaces_actor.get(cloudspace_id)

        self.vars["space.free.tcp.addr"]=space["publicipaddress"]
        self.vars["space.ip.pub"]=space["publicipaddress"]

        pubip=space["publicipaddress"]

        portforwarding_actor = api.getActor('cloudapi', 'portforwarding')

        tcpports={}
        udpports={}
        for item in portforwarding_actor.list(cloudspace_id):
            if item['publicIp']==pubip:
                if item['protocol']=="tcp":
                    tcpports[int(item['publicPort'])]=True
                elif item['protocol']=="udp":
                    udpports[int(item['publicPort'])]=True

        for i in range(mmin,mmax):
            if i not in tcpports and i not in udpports:
                break

        if i>mmax-1:
            raise RuntimeError("E:cannot find free tcp or udp port.")


        self.vars["space.free.tcp.port"]=str(i)
        self.vars["space.free.udp.port"]=str(i)

        return self.vars

    def listPortforwarding(self,spacesecret, name,**args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')

        machine = machines_actor.get(machine_id)
        if machine['cloudspaceid'] != cloudspace_id:
            return 'Machine %s does not belong to cloudspace whose secret is given' % name

        portforwarding_actor = api.getActor('cloudapi', 'portforwarding')
        items=portforwarding_actor.list(cloudspace_id)

        if len(machine["interfaces"])>0:
            local_ipaddr=machine["interfaces"][0]['ipAddress'].strip()
        else:
            raise RuntimeError("cannot find local ip addr")

        items=[]
        for item in portforwarding_actor.list(cloudspace_id):
            if item['localIp']==local_ipaddr:
                items.append(item)
        return items

    def _getSSHConnection(self, spacesecret, name, sshkey=None, **args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)

        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')

        machine = machines_actor.get(machine_id)
        if machine['cloudspaceid'] != cloudspace_id:
            return 'Machine %s does not belong to cloudspace whose secret is given' % name


        print("RECREATE SSH CONNECTION")
        portforwarding_actor = api.getActor('cloudapi', 'portforwarding')
        items=portforwarding_actor.list(cloudspace_id)

        if len(machine["interfaces"])>0:
            local_ipaddr=machine["interfaces"][0]['ipAddress'].strip()
        else:
            raise RuntimeError("cannot find local ip addr")

        #remove leftovers
        for item in items:
            if item['localIp'].strip()==local_ipaddr and int(item['localPort'])==22:
                self.sendUserMessage("Delete existing PFW rule:%s %s"%(item['localIp'],22),args=args)
                try:
                    portforwarding_actor.delete(cloudspace_id,item["id"])
                except Exception as e:
                    self.sendUserMessage("Warning: could not delete.",args=args)

        tempportdict=self.getFreeIpPort(spacesecret,mmin=1500,mmax=1999,**args)
        tempport=tempportdict['space.free.tcp.port']

        counter=1
        localIP=machine["interfaces"][0]["ipAddress"]
        while localIP=="" or localIP.lower()=="undefined":
            print("NO IP YET")
            machine = machines_actor.get(machine_id)
            counter+=1
            time.sleep(0.5)
            if counter>100:
                raise RuntimeError("E:could not find ip address for machine:%s"%name)
            localIP=machine["interfaces"][0]["ipAddress"]

        self.createTcpPortForwardRule(spacesecret, name, 22, pubipport=tempport,**args)

        cloudspace = cloudspaces_actor.get(cloudspace_id)
        pubip=cloudspace['publicipaddress']

        connectionAddr = cloudspace['publicipaddress']
        connectionPort = tempport
        counter = 0
        while counter < 3:
            if not j.system.net.waitConnectionTest(cloudspace['publicipaddress'], int(tempport), 5):
                # if we can't connect with public IP, it probably means we try to access the vm from inside the cloudspace with another vm
                # so we try to connect using the private ip
                if not j.system.net.waitConnectionTest(local_ipaddr, 22, 5):
                    if counter >=3:
                        # if still can't connect, then it's an error
                        raise RuntimeError("E:Failed to connect to %s" % (tempport))
                else:
                    connectionAddr = local_ipaddr
                    connectionPort = 22
                    break
                counter = counter+1
            else:
                break

        # if we don't specify the key to push
        # create one first
        key = None
        if sshkey is None:
            keyloc = "/root/.ssh/id_rsa.pub"

            if not j.system.fs.exists(path=keyloc):
                j.system.process.executeWithoutPipe("ssh-keygen -t rsa")
                if not j.system.fs.exists(path=keyloc):
                    raise RuntimeError("cannot find path for key %s, was keygen well executed"%keyloc)

            j.system.fs.chmod("/root/.ssh/id_rsa", 0o600)
            key = j.system.fs.fileGetContents(keyloc)
        else:
            key = sshkey

        rloc = "/root/.ssh/authorized_keys"

        ssh_connection = j.remote.cuisine.api

        ssh_connection.mode_sudo()

        username, password = machine['accounts'][0]['login'], machine['accounts'][0]['password']
        ssh_connection.fabric.api.env['password'] = password
        ssh_connection.fabric.api.env['connection_attempts'] = 5
        ssh_connection.connect('%s:%s' % (connectionAddr, connectionPort), username)

        name = name.replace('_', '').replace(' ','-')
        ssh_connection.run('echo "%s" > /etc/hostname' % name)
        ssh_connection.run('hostname %s' % name)
        ssh_connection.run('echo "127.0.0.1 %s" >> /etc/hosts' % name)

        # will overwrite all old keys
        ssh_connection.file_write(rloc, key)

        return ssh_connection

    def execSshScript(self, spacesecret, name,**args):

        ssh_connection=self._getSSHConnection(spacesecret,name,**args)

        if "lines" in args:
            script=args["lines"]
            out=""
            for line in script.split("\n"):
                line=line.strip()
                if line.strip()=="":
                    continue
                if line[0]=="#":
                    continue
                out+="%s\n"%line
                print(line)

                result= ssh_connection.run(line+"\n")
                out+="%s\n"%result
                print(result)

        elif "script" in args:
            script=args["script"]
            script="set +ex\n%s"%script
            print("SSHPREPARE:")
            print(script)
            ssh_connection.file_write("/tmp/do.sh",script)
            ssh_connection.fabric.context_managers.show("output")

            from io import StringIO
            import sys

            sys.stdout=self.stdout

            # ssh_connection.run("sh /tmp/do.sh", pty=False, combine_stderr=True,stdout=fh)
            try:
                out=ssh_connection.run("sh /tmp/do.sh",combine_stderr=True)
            except BaseException as e:
                sys.stdout=self.stdout.prevout
                if self.stdout.lastlines.strip()!="":
                    msg="Could not execute sshscript:\n%s\nError:%s\n"%(script,self.stdout.lastlines)
                    self.action.raiseError(msg)
                    self.stdout.lastlines=""
                print(e)
                raise RuntimeError("E:Could not execute sshscript, errors.")
            sys.stdout=self.stdout.prevout

        else:
            raise RuntimeError("E:Could not find param script or lines")


        return out
