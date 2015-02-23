from JumpScale import j
platformid = None
import sys

def cb():
        from .ubuntu.Ubuntu import Ubuntu
        return Ubuntu()

j.base.loader.makeAvailable(j, 'system.platform')
if not sys.platform.startswith("win"):
    try:
        import lsb_release
        platformid = lsb_release.get_distro_information()['ID']
    except ImportError:
        exitcode, platformid = j.system.process.execute('lsb_release -i -s', False)
        platformid = platformid.strip()
    if platformid in ('Ubuntu', 'LinuxMint'):
        j.system.platform._register('ubuntu', cb)
