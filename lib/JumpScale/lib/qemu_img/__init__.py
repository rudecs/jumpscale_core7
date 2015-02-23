from JumpScale import j

def cb():
    from .qemu_img import QemuImg
    return QemuImg()

j.base.loader.makeAvailable(j, 'system.platform')
j.system.platform._register('qemu_img', cb)

