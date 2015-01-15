from fabric.api import task, run

@task
def setupNetwork(ifaces):
    for iface, config in ifaces.iteritems():
        if iface == 'eth1':
            run('netsh interface ip set address name="%s" static %s %s gateway=%s' % (iface, config[0], config[1], config[2]))
        else:
            run('netsh interface ip set address name="%s" static %s %s' % (iface, config[0], config[1]))