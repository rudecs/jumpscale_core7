from JumpScale import j


class PerfTestTools():
    def __init__(self,node):
        self.node=node

    def sequentialWriteReadBigBlock(self,nrfiles=1):
        """
        disknr starts with 1
        """
        for disk in self.node.disks:
            print "SEQUENTIAL WRITE %s %s"%(self.node,disk)
            
            path="%s/testfile"%disk.mountpath
            filepaths=""
            for i in range(nrfiles+1):
                filepaths+="-F '%s%s' "%(path,(i))

            cmd="iozone -i 0 -i 1 -R -s 1000M -I -k -l 5 -O -r 256k -t %s -T %s"%(nrfiles,filepaths)
            disk.execute(cmd)

