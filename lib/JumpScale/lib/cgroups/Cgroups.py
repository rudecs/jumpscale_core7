#!/usr/bin/env python
from JumpScale import j

class Cgroups():

    def __init__(self):
        pass

    def execute(self, command):
        (exitcode, stdout, stderr) = j.system.process.run(command, showOutput=False, captureOutput=True, stopOnError=False)
        if exitcode != 0:
            raise RuntimeError("Failed to execute %s: Error: %s, %s" % (command, stdout, stderr))
        return stdout

    def create(self, name):
        command =  "cgcreate -g cpuset,memory:{name}".format(name=name)
        return self.execute(command)
       
    def set_mem_limit(self, name, size_in_mega):
        command = "cgset -r memory.limit_in_bytes={size}M {name}".format(name=name, size=size_in_mega)
        return self.execute(command)
    
    def set_cpu_cores(self, name, cores):
        command = "cgset -r cpuset.cpus={cores} {name}".format(name=name, cores=cores)
        return self.execute(command)

    def add_processes(self, name, processes_pids):
        # processes_pids are pids for the processes as a list
        processes_pids = map(lambda x: str(x), processes_pids)
        processes_pids = " ".join(processes_pids)
        command = "cgclassify -g cpu,memory:{name} {processes_pids}".format(name, processes_pids)
        return self.execute(command)

    def get_cpu_mem(self, name):
        command = "cgget -r memory.limit_in_bytes -r cpuset.cpus {name}".format(name=name)
        return self.execute(command)
