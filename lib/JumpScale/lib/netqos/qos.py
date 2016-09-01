from JumpScale import j


class QOS(object):
    def limitNic(self, name, rate, burst, prio=100):
        self.removeLimit(name)
        cmd '''\
        # first create ingress policer
        tc qdisc add dev {iface} handle ffff: ingress

        # allow ssh to continue to work
        tc filter add dev {iface} parent ffff: protocol ip \
            pref {prio} u32 match ip dport 22 0xffff flowid 1: \
            police rate 100mbit burst 100mbit \
            mpu 0 action continue continue
        # same for 3389 (RDP) ?
        tc filter add dev {iface} parent ffff: protocol ip \
            pref {prio} u32 match ip dport 3389 0xffff flowid 1: \
            police rate 100mbit burst 100mbit \
            mpu 0 action continue continue

        # police everything else FROM the VM (really tight, most protocols will stop working)
        tc filter add dev {iface} parent ffff:  u32 \
            match u32 0 0 police rate {rate} burst {burst} \
            flowid 1: action drop continue
        '''.format(iface=name, prio=prio, burst=burst, rate=rate)
        j.system.process.execute(cmd)

    def removeLimit(self, name):
        cmd = '''\
        # Delete limit
        tc qdisc del dev {iface} root
        '''.format(iface=name)
        j.system.process.execute(cmd, dieOnNonZeroExitCode=False)
