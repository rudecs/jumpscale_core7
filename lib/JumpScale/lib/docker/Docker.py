#!/usr/bin/env python
from JumpScale import j
import sys,time
import JumpScale.lib.diskmanager
import os
# import JumpScale.baselib.netconfig
import netaddr
import JumpScale.baselib.remote
import docker
import time
import json

class Docker():

    def __init__(self):
        self._basepath = "/mnt/vmstor/docker"
        self._prefix=""
        self.client = docker.Client(base_url='unix://var/run/docker.sock')
        self.remote = {'host': 'localhost', 'port': 0}

    def connectRemoteTCP(self, address, port):
        url = '%s:%s' % (address, port)
        self.client = docker.Client(base_url=url)
        self.remote = {'host': address, 'port': port}

    def _execute(self, command):
        env = os.environ.copy()
        env.pop('PYTHONPATH', None)
        (exitcode, stdout, stderr) = j.system.process.run(command, showOutput=False, captureOutput=True, stopOnError=False, env=env)
        if exitcode != 0:
            raise RuntimeError("Failed to execute %s: Error: %s, %s" % (command, stdout, stderr))
        return stdout

    def run(self,name,cmd):
        cmd2="docker exec -i -t %s %s"%(name,cmd)
        j.do.executeInteractive(cmd2)

    def execute(self,name,path):
        """
        execute file in docker
        """
        self.copy(name,path,path)
        j.tools.docker.run(name,"chmod 770 %s;%s"%(path,path))

    def copy(self, name, src, dest):
        rndd = j.base.idgenerator.generateRandomInt(10, 1000000)
        temp = "/var/docker/%s/%s" % (name, rndd)
        j.system.fs.createDir(temp)
        source_name = j.system.fs.getBaseName(src)
        if j.system.fs.isDir(src):
            j.do.copyTree(src, j.system.fs.joinPaths(temp, source_name))
        else:
            j.do.copyFile(src, j.system.fs.joinPaths(temp, source_name))

        ddir = j.system.fs.getDirName(dest)
        cmd = "mkdir -p %s" % (ddir)
        self.run(name, cmd)

        cmd = "cp -r /var/jumpscale/%s/%s %s" % (rndd, source_name, dest)
        self.run(name, cmd)
        j.do.delete(temp)


    @property
    def basepath(self):
        if not self._basepath:
            self._basepath = j.application.config['system'].get('docker_basepath', '/mnt/vmstor/docker')
        return self._basepath

    def _getChildren(self,pid,children):
        process=j.system.process.getProcessObject(pid)
        children.append(process)
        for child in process.get_children():
            children=self._getChildren(child.pid,children)
        return children

    def _get_rootpath(self,name):
        rootpath=j.system.fs.joinPaths(self.basepath, '%s%s' % (self._prefix, name), 'rootfs')
        return rootpath

    def _getMachinePath(self,machinename,append=""):
        if machinename=="":
            raise RuntimeError("Cannot be empty")
        base = j.system.fs.joinPaths( self.basepath,'%s%s' % (self._prefix, machinename))
        if append!="":
            base=j.system.fs.joinPaths(base,append)
        return base

    def list(self):
        """
        return list of names
        """
        res={}
        for item in self.client.containers():
            res[str(item["Names"][0].strip("/").strip())]=str(item["Id"].strip())
        return res

    def ps(self, all=False):
        """
        return detailed info
        """
        return self.client.containers(all=all)

    def inspect(self,name):
        return self.client.inspect_container(name)

    def getInfo(self,name):
        for item in self.ps():
            if "/%s"%name in item["Names"]:
                return item
        raise RuntimeError("Could not find info from '%s' (docker)"%name)

    def getIp(self,name):
        res=self.inspect(name)
        return res['NetworkSettings']['IPAddress']

    def getProcessList(self, name, stdout=True):
        """
        @return [["$name",$pid,$mem,$parent],....,[$mem,$cpu]]
        last one is sum of mem & cpu
        """
        raise RuntimeError("not implemented")
        pid = self.getPid(name)
        children = list()
        children=self._getChildren(pid,children)
        result = list()
        pre=""
        mem=0.0
        cpu=0.0
        cpu0=0.0
        prevparent=""
        for child in children:
            if child.parent.name != prevparent:
                pre+=".."
                prevparent=child.parent.name
            # cpu0=child.get_cpu_percent()
            mem0=int(round(child.get_memory_info().rss/1024,0))
            mem+=mem0
            cpu+=cpu0
            if stdout:
                print(("%s%-35s %-5s mem:%-8s" % (pre,child.name, child.pid, mem0)))
            result.append([child.name,child.pid,mem0,child.parent.name])
        cpu=children[0].get_cpu_percent()
        result.append([mem,cpu])
        if stdout:
            print(("TOTAL: mem:%-8s cpu:%-8s" % (mem, cpu)))
        return result

    def exportRsync(self,name,backupname,key="pub"):
        raise RuntimeError("not implemented")
        self.removeRedundantFiles(name)
        ipaddr = j.application.config['system'].get('jssync_addr')
        path=self._getMachinePath(name)
        if not j.system.fs.exists(path):
            raise RuntimeError("cannot find machine:%s"%path)
        if backupname[-1]!="/":
            backupname+="/"
        if path[-1]!="/":
            path+="/"
        cmd="rsync -a %s %s::upload/%s/images/%s --delete-after --modify-window=60 --compress --stats  --progress --exclude '.Trash*'"%(path,ipaddr,key,backupname)
        # print cmd
        j.system.process.executeWithoutPipe(cmd)

    def _btrfsExecute(self,cmd):
        cmd="btrfs %s"%cmd
        print(cmd)
        return self._execute(cmd)

    def btrfsSubvolList(self):
        raise RuntimeError("not implemented")
        out=self._btrfsExecute("subvolume list %s"%self.basepath)
        res=[]
        for line in out.split("\n"):
            if line.strip()=="":
                continue
            if line.find("path ")!=-1:
                path=line.split("path ")[-1]
                path=path.strip("/")
                path=path.replace("lxc/","")
                res.append(path)
        return res

    def btrfsSubvolNew(self,name):
        raise RuntimeError("not implemented")
        if not self.btrfsSubvolExists(name):
            cmd="subvolume create %s/%s"%(self.basepath,name)
            self._btrfsExecute(cmd)

    def btrfsSubvolCopy(self,nameFrom,NameDest):
        raise RuntimeError("not implemented")
        if not self.btrfsSubvolExists(nameFrom):
            raise RuntimeError("could not find vol for %s"%nameFrom)
        if j.system.fs.exists(path="%s/%s"%(self.basepath,NameDest)):
            raise RuntimeError("path %s exists, cannot copy to existing destination, destroy first."%nameFrom)
        cmd="subvolume snapshot %s/%s %s/%s"%(self.basepath,nameFrom,self.basepath,NameDest)
        self._btrfsExecute(cmd)

    def btrfsSubvolExists(self,name):
        raise RuntimeError("not implemented")
        subvols=self.btrfsSubvolList()
        # print subvols
        return name in subvols

    def btrfsSubvolDelete(self,name):
        raise RuntimeError("not implemented")
        if self.btrfsSubvolExists(name):
            cmd="subvolume delete %s/%s"%(self.basepath,name)
            self._btrfsExecute(cmd)
        path="%s/%s"%(self.basepath,name)
        if j.system.fs.exists(path=path):
            j.system.fs.removeDirTree(path)
        if self.btrfsSubvolExists(name):
            raise RuntimeError("vol cannot exist:%s"%name)

    def removeRedundantFiles(self,name):
        raise RuntimeError("not implemented")
        basepath=self._getMachinePath(name)
        j.system.fs.removeIrrelevantFiles(basepath,followSymlinks=False)

        toremove="%s/rootfs/var/cache/apt/archives/"%basepath
        j.system.fs.removeDirTree(toremove)

    def importRsync(self,backupname,name,basename="",key="pub"):
        """
        @param basename is the name of a start of a machine locally, will be used as basis and then the source will be synced over it
        """
        raise RuntimeError("not implemented")
        ipaddr = j.application.config['system'].get('jssync_addr')
        path=self._getMachinePath(name)

        self.btrfsSubvolNew(name)

        # j.system.fs.createDir(path)

        if backupname[-1]!="/":
            backupname+="/"
        if path[-1]!="/":
            path+="/"

        if basename!="":
            basepath=self._getMachinePath(basename)
            if basepath[-1]!="/":
                basepath+="/"
            if not j.system.fs.exists(basepath):
                raise RuntimeError("cannot find base machine:%s"%basepath)
            cmd="rsync -av -v %s %s --delete-after --modify-window=60 --size-only --compress --stats  --progress"%(basepath,path)
            print(cmd)
            j.system.process.executeWithoutPipe(cmd)

        cmd="rsync -av -v %s::download/%s/images/%s %s --delete-after --modify-window=60 --compress --stats  --progress"%(ipaddr,key,backupname,path)
        print(cmd)
        j.system.process.executeWithoutPipe(cmd)

    def exportTgz(self,name,backupname):
        raise RuntimeError("not implemented")
        self.removeRedundantFiles(name)
        path=self._getMachinePath(name)
        bpath= j.system.fs.joinPaths(self.basepath,"backups")
        if not j.system.fs.exists(path):
            raise RuntimeError("cannot find machine:%s"%path)
        j.system.fs.createDir(bpath)
        bpath= j.system.fs.joinPaths(bpath,"%s.tgz"%backupname)
        cmd="cd %s;tar Szcf %s ."%(path,bpath)
        j.system.process.executeWithoutPipe(cmd)
        return bpath

    def importTgz(self,backupname,name):
        raise RuntimeError("not implemented")
        path=self._getMachinePath(name)
        bpath= j.system.fs.joinPaths(self.basepath,"backups","%s.tgz"%backupname)
        if not j.system.fs.exists(bpath):
            raise RuntimeError("cannot find import path:%s"%bpath)
        j.system.fs.createDir(path)

        cmd="cd %s;tar xzvf %s -C ."%(path,bpath)
        j.system.process.executeWithoutPipe(cmd)

    def create(self, name="", ports="", vols="", volsro="", stdout=True, base="despiegk/mc", nameserver=["8.8.8.8"],
               replace=True, cpu=None, mem=0, jumpscale=False, ssh=True, myinit=True, sharecode=False, mapping=True):

        """
        @param ports in format as follows  "22:8022 80:8080"  the first arg e.g. 22 is the port in the container
        @param vols in format as follows "/var/insidemachine:/var/inhost # /var/1:/var/1 # ..."   '#' is separator
        """
        name = name.lower().strip().replace('_', '')

        print '[+] creating docker: %s' % name

        running=self.list()
        running=list(running.keys())
        if not replace:
            if name in running:
                j.events.opserror_critical("Cannot create machine with name %s, because it does already exists.")

        self.destroy(name)

        if vols==None:
            vols=""
        if volsro==None:
            volsro=""
        if ports==None:
            ports=""

        if mem==None:
            mem=0

        if int(mem)>0:
            mem=int(mem)*1024

        portsdict={}
        if len(ports)>0:
            items=ports.split(" ")
            for item in items:
                key,val=item.split(":",1)
                portsdict[int(key)]=int(val)

        if ssh:
            if 22 not in portsdict:
                for port in range(9022,9190):
                    if not j.system.net.tcpPortConnectionTest(self.remote['host'], port):
                        portsdict[22]=port
                        print '[+] ssh port autodetected: %s' % port
                        break

        volsdict={}
        if len(vols)>0:
            items=vols.split("#")
            for item in items:
                key,val=item.split(":",1)
                volsdict[str(key).strip()]=str(val).strip()

        if mapping:
                j.system.fs.createDir("/var/jumpscale")
                if "/var/jumpscale" not in volsdict:
                    volsdict["/var/jumpscale"]="/var/docker/%s"%name
                j.system.fs.createDir("/var/docker/%s"%name)

                tmppath="/tmp/dockertmp/%s"%name
                j.system.fs.createDir(tmppath)
                volsdict[tmppath]="/tmp"

        if sharecode and j.system.fs.exists(path="/opt/code"):
            if "/opt/code" not in volsdict:
                volsdict["/opt/code"]="/opt/code"

        volsdictro={}
        if len(volsro)>0:
            items=volsro.split("#")
            for item in items:
                key,val=item.split(":",1)
                volsdictro[str(key).strip()]=str(val).strip()

        print '[+] volume map:'
        for src1, dest1 in volsdict.items():
            print "[+]   %s -> %s" % (src1, dest1)

        binds={}
        volskeys=[] #is location in docker

        for key,path in list(volsdict.items()):
            j.system.fs.createDir(path) #create the path on hostname
            binds[path]={"bind":key, "mode":"rw"}
            volskeys.append(key)

        for key,path in list(volsdictro.items()):
            j.system.fs.createDir(path) #create the path on hostname
            binds[path]={"bind":key, "mode":"ro"}
            volskeys.append(key)

        # volskeys=volsdict.keys()+volsdictro.keys()

        if base not in self.getImages():
            print '[+] downloading image'
            self.pull(base)

        if myinit:
            cmd="sh -c \"mkdir -p /var/run/screen;chmod 777 /var/run/screen; /var/run/screen;exec >/dev/tty 2>/dev/tty </dev/tty && /sbin/my_init -- /usr/bin/screen -s bash\""
            cmd="sh -c \" /sbin/my_init -- bash -l\""
            #echo -e 'gig1234\ngig1234' | passwd root;
            # cmd="sh -c \"exec >/dev/tty 2>/dev/tty </dev/tty && /sbin/my_init -- /usr/bin/screen -s bash\""
        else:
            cmd=None

        # mem=1000000
        print '[+] installing docker %s (from: %s)' % (name, base)

        res=self.client.create_container(image=base, command=cmd, hostname=name, user="root", \
                detach=False, stdin_open=False, tty=True, mem_limit=mem, ports=list(portsdict.keys()), environment=None, volumes=volskeys,  \
                network_disabled=False, name=name, entrypoint=None, cpu_shares=cpu, working_dir=None, domainname=None, memswap_limit=0)

        if res["Warnings"]!=None:
            raise RuntimeError("Could not create docker, res:'%s'"%res)

        id=res["Id"]

        res=self.client.start(container=id, binds=binds, port_bindings=portsdict, lxc_conf=None, \
            publish_all_ports=False, links=None, privileged=False, dns=nameserver, dns_search=None, volumes_from=None, network_mode=None)

        if ssh:
            portfound=0
            for internalport,extport in list(portsdict.items()):
                if internalport==22:
                    print '[+] checking for external ssh access: port %s' % extport
                    portfound=extport
                    if j.system.net.waitConnectionTest(self.remote['host'], extport, timeout=10) == False:
                        log = self.client.logs(name)
                        j.events.opserror_critical("Could not connect to external port on docker:'%s', docker prob not running.\nStartuplog:\n%s\n"%(extport,log),category="docker.create")

            time.sleep(0.5)

            self.pushSSHKey(name)

            if jumpscale:
                self.installJumpscale(name)

            return portfound

        else:
            return None



        # return self.getIp(name)

    def installJumpscale(self,name):
        print "Install jumpscale7 on python 2"
        c=self.getSSH(name)
        hrdf="/opt/jumpscale7/hrd/system/whoami.hrd"
        if j.system.fs.exists(path=hrdf):
            c.dir_ensure("/opt/jumpscale7/hrd/system",True)
            c.file_upload(hrdf,hrdf)
        c.fabric.state.output["running"]=True
        c.fabric.state.output["stdout"]=True
        c.run("cd /opt/code/github/jumpscale7/jumpscale_core7/install/ && bash install.sh")

    def getImages(self):
        images=[str(item["RepoTags"][0]).replace(":latest","") for item in self.client.images() if item['RepoTags']]
        return images

    def removeImages(self,tag="<none>:<none>"):
        for item in self.client.images():
            if tag in item["RepoTags"]:
                self.client.remove_image(item["Id"])


    def setHostName(self,name):
        raise RuntimeError("not implemented")
        lines=j.system.fs.fileGetContents("/etc/hosts")
        out=""
        for line in lines.split("\n"):
            if line.find(name)!=-1:
                continue
            out+="%s\n"%line
        out+="%s      %s\n"%(self.getIp(name),name)
        j.system.fs.writeFile(filename="/etc/hosts",contents=out)

    def getPubPortForInternalPort(self,name,port):
        info=self.getInfo(name)
        for port2 in info["Ports"]:
            if int(port2["PrivatePort"])==int(port):
                if "PublicPort" not in port2:
                    j.events.inputerror_critical("cannot find publicport for ssh?")
                return port2["PublicPort"]

    def pushSSHKey(self,name):
        # path=j.system.fs.joinPaths(self._get_rootpath(name),"root",".ssh","authorized_keys")
        privkeyloc="/root/.ssh/id_rsa"
        keyloc=privkeyloc + ".pub"

        if not j.system.fs.exists(path=keyloc):
            j.system.process.executeWithoutPipe("ssh-keygen -t rsa -f %s -N ''" % privkeyloc)
            if not j.system.fs.exists(path=keyloc):
                raise RuntimeError("cannot find path for key %s, was keygen well executed"%keyloc)
        key=j.system.fs.fileGetContents(keyloc)
        # j.system.fs.writeFile(filename=path,contents="%s\n"%content)

        j.system.fs.writeFile(filename="/root/.ssh/known_hosts", contents="")

        c=j.remote.cuisine.api
        c.fabric.api.env['password'] = "gig1234"
        c.fabric.api.env['connection_attempts'] = 5

        c.fabric.state.output["running"]=False
        c.fabric.state.output["stdout"]=False

        ssh_port=self.getPubPortForInternalPort(name,22)
        if ssh_port==None:
            j.events.opserror_critical("cannot find pub port ssh")

        c.connect('%s:%s' % (self.remote['host'], ssh_port), "root")

        counter=0
        connect=False
        time.sleep(1)
        while counter<20 and connect==False:
            try:
                counter+=1
                print '[+] connecting ssh docker'
                c.ssh_authorize("root", key)

            except Exception,e:
                time.sleep(1)
                continue
            connect=True

        if connect==False:
            j.events.opserror_critical("Could not connect to ssh on localhost on port %s"%ssh_port)


        c.fabric.state.output["running"]=True
        c.fabric.state.output["stdout"]=True

        return key

    def getSSH(self,name,stdout=False):
        ssh_port=self.getPubPortForInternalPort(name,22)
        c=j.remote.cuisine.api
        c.fabric.api.env['connection_attempts'] = 2
        c.fabric.state.output["running"]=stdout
        c.fabric.state.output["stdout"]=stdout
        c.connect('%s:%s' % ("localhost", ssh_port), "root")
        return c

    def destroyall(self):
        running=self.list()
        for item in list(running.keys()):
            self.destroy(item)

        # startpath="/mnt/vmstor"
        # cmd="btrfs subvol list %s"%startpath
        # res=self.execute(cmd)
        # for line in res.split("\n"):
        #     if line.find("path") != -1:
        #         part=line.split("path",1)[1]
        #         if part.find("docker2") != -1:
        #             # id=line.split("gen")[0].strip("ID").strip()
        #             part=part.strip()
        #             path="%s/%s"%(startpath,part)
        #             command="btrfs subvol delete %s"%path
        #             print j.system.process.execute(command, dieOnNonZeroExitCode=False, outputToStdout=False, useShell=False, ignoreErrorOutput=False)

    def destroy(self,name):
        running=self.list()

        if name in list(running.keys()):
            idd=running[name]
            self.client.kill(idd)
            self.client.remove_container(idd)

        cmd="docker rm %s"%name
        j.system.process.execute(cmd,dieOnNonZeroExitCode=False)

    def stop(self,name):
        running=self.list()
        if name in list(running.keys()):
            idd=running[name]
            self.client.kill(idd)

    def restart(self,name):
        self.client.restart(name)

    def commit(self,name,imagename):
        cmd="docker rmi %s"%imagename
        j.system.process.execute(cmd,dieOnNonZeroExitCode=False)
        cmd="docker commit %s %s"%(name,imagename)
        j.system.process.executeWithoutPipe(cmd)

    def pull(self,imagename):
        self.client.import_image_from_image(imagename)

    def uploadFile(self, name, source, dest):
        """
        put a file located at source on the host to dest into the container
        """
        self.copy(name, source, dest)

    def downloadFile(self, name, source, dest):
        """
        get a file located at source in the host to dest on the host

        """
        conn = self.getSSH(name)
        if not conn.file_exists(source):
            j.events.inputerror_critical(msg="%s not found in container" % source)
        ddir=j.system.fs.getDirName(dest)
        j.system.fs.createDir(ddir)
        content = conn.file_read(source)
        j.system.fs.writeFile(dest, content)
