from fabric.api import task, run, settings


@task
def setupNetwork(ifaces):
    with settings(user='Administrator'):
        for iface, config in ifaces.iteritems():
            if iface == 'eth1':
                run('netsh interface ip set address name="%s" static %s %s gateway=%s' % (
                    iface, config[0], config[1], config[2]), timeout=1)
            else:
                run('netsh interface ip set address name="%s" static %s %s' %
                    (iface, config[0], config[1]), timeout=1)


@task
def pushSshKey(sshkey):
    with settings(user='Administrator'):
        run('touch /etc/authorized_keys; echo "%s" > /etc/authorized_keys' %
            sshkey)
