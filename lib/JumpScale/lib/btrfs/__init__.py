from JumpScale import j

def cb():
    from  .BtrfsExtension import BtrfsExtension
    return BtrfsExtension()

j.system._register('btrfs', cb)
