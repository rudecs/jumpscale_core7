from JumpScale import j

def cb():
    from KVM import KVM
    return KVM()

j.base.loader.makeAvailable(j, 'system.platform')
j.system.platform._register('kvm', cb)

