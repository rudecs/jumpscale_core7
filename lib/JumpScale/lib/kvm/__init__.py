from JumpScale import j
j.base.loader.makeAvailable(j, 'system.platform.kvm')
from KVM import KVM
j.system.platform.kvm = KVM()

