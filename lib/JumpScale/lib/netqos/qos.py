from JumpScale import j


class QOS(object):
    def limitNic(self, name, rate, burst, prio=100):
        self.removeLimit(name)
        cmd = '''\
delay=400ms
# Add 2 rules, one to narrow down bw utilisation in any case and one to still allow interactivity for ssh to the vm (we could envision rdp as a third rule)

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
tc filter add dev ${iface} parent ffff:  u32 \
    match u32 0 0 police rate {rate} burst {burst} \
    flowid 1: action drop continue

# Create Token Bucket Filter
tc qdisc add dev {iface} root handle 1: prio

# classify traffic
# rate traffic to vm for interactive (22,3389)
tc qdisc add dev {iface} parent 1:2 handle 20: tbf \
    rate {rate} buffer 1600 limit 3000
# all the rest sluggish
tc qdisc add dev {iface} parent 1:3 handle 30: netem \
    delay {delay}
# set filters
tc filter add dev {iface} protocol ip parent 1: \
    prio 2 route flowid 1:1
# send dport 22 and 3389 TO vm on the happy path
tc filter add dev {iface} protocol ip \
    parent 1: prio 1 u32 match ip dport 22 0xffff flowid 1:2
tc filter add dev {iface} protocol ip \
    parent 1: prio 1 u32 match ip dport 3389 0xffff flowid 1:2
# send all the rest to the delayer
tc filter add dev {iface} protocol ip \
    parent 1: prio 1 u32 match u32 0 0 flowid 1:3

        '''.format(iface=name, prio=prio, burst=burst, rate=rate)
        j.system.process.execute(cmd)

    def removeLimit(self, name):
        cmd = '''\
# Delete limit
tc qdisc del dev {iface} root
tc qdisc del dev {iface} parent ffff:
        '''.format(iface=name)
        j.system.process.execute(cmd, dieOnNonZeroExitCode=False)
