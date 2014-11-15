

'''Process creation helper

This script can be spawned as an intermediate process when creating a new
process to be able to daemonize the result process, or setuid/setgid the result
process.
'''

import os
import os.path
import sys
import time
import itertools

def find_gids_for_uid(uid):
    '''Find all GIDs of groups the user with given name belongs to

    @param uid: User UID
    @type uid: number

    @returns: GIDs of all groups the user belongs to
    @rtype: list<number>
    '''
    import grp
    import pwd

    # Primary group
    user = pwd.getpwuid(uid)
    yield user.pw_gid

    username = user.pw_name

    for group in grp.getgrall():
        if username in group.gr_mem:
            yield group.gr_gid


def change_uid_gid(uid, gid):
    '''Impersonate the given UID and/or GID

    Do note this will only work if the current process has the privileges to
    impersonate this user or group.

    Here's how things are processed. Let's assume we're currently running as
    root (uid=0, groups=root(0)), and there's one more user called 'test'
    (uid=1000, gid=1001, groups=test1(1001), test2(1002)).

    +=======================================================+
    | Arguments   | Resulting process environment           |
    |             |                                         |
    | UID  | GID  | UID  | GID  | Extra groups              |
    +======+======+======+======+===========================+
    | None | None | 0    | 0    | root                      |
    +-------------+------+------+---------------------------+
    | 0    | None | 0    | 0    | root                      |
    +-------------+------+------+---------------------------+
    | None | 0    | 0    | 0    | root                      |
    +-------------+------+------+---------------------------+
    | 0    | 0    | 0    | 0    | root                      |
    +-------------+------+------+---------------------------+
    | 1000 | None | 1000 | 1001 | test1, test2              |
    +-------------+------+------+---------------------------+
    | None | 1001 | 0    | 1001 | root                      |
    +-------------+------+------+---------------------------+
    | 1000 | 1001 | 1000 | 1001 | test1, test2              |
    +-------------+------+------+---------------------------+
    | 1000 | 1002 | 1000 | 1002 | test1, test2              |
    +-------------+------+------+---------------------------+
    | 1000 | 0    | 1000 | 0    | test1, test2, root        |
    +-------------+------+------+---------------------------+

    @param uid: UID of the user to impersonate
    @type uid: number
    @param gid: GID of the group to impersonate
    @type gid: number
    '''
    if uid is None and gid is None:
        # Nothing to do
        return

    if uid is not None:
        # Set up correct groups
        #
        # We need to make sure correct GIDs are set. Here's how it works:
        #
        # * If a GID is given, this one is added to the set of target GIDs
        # * The GIDs of all groups the user with target UID belongs to is added
        #   to the set of target GIDs
        #
        # Do note we're not using libc.initgroups() since this doesn't take
        # primary groups into account, and only works with /etc/group
        if gid is not None:
            standard_gids = (gid, )
        else:
            standard_gids = tuple()

        gids = itertools.chain(standard_gids, find_gids_for_uid(uid))

        # Calculate unique list of GIDs
        gids = set(gids)

        if not hasattr(os, 'setgroups'):
            raise RuntimeError('setgroups() not available on this platform')

        os.setgroups(tuple(gids))

    # Note: we need to call setgid() before calling setuid() because it might be
    # possible setgid() fails once we impersonated another user
    if gid is not None and not hasattr(os, 'setgid'):
        raise RuntimeError('GID provided but setgid() not available on this '
                           'platform')
    if gid is not None:
        os.setgid(gid)

    if uid is not None and gid is None:
        # Set primary group to GID of given UID
        if not hasattr(os, 'setgid'):
            raise RuntimeError('setgid() not available on this platform')

        import pwd
        user = pwd.getpwuid(uid)
        os.setgid(user.pw_gid)

    if uid is not None and not hasattr(os, 'setuid'):
        raise RuntimeError('UID provided by setuid() not available on this '
                           'platform')
    if uid is not None:
        os.setuid(uid)


def daemonize(stdout, stderr, chdir='/', umask=0):
    '''Daemonize a process using a double fork

    This method will fork the current process to create a daemon process.
    It will perform a double fork(2), chdir(2) to the given folder (or not
    chdir at all if the C{chdir} argument is C{None}), and set the new
    process umask(2) to the value of the C{umask} argument, or not reset
    it if this argument is -1.

    The stdout and stderr arguments can be used to output the output to the
    corresponding streams of the daemon process to files at the provided
    location. Make sure the parent folder of these files already exists. When
    set to None, all output will vanish.

    While forking, a setsid(2) call will be done to become session leader
    and detach from the controlling TTY.

    In the child process, all existing file descriptors will be closed,
    including stdin, stdout and stderr, which will be re-opened to
    /dev/null, unless a corresponding parameter is provided as an argument to
    this function.

    The method returns a tuple<bool, number>. If the first item is True,
    the current process is the daemonized process. If it is False,
    the current process is the process which called the C{daemonize}
    method, which can most likely be closed now. The second item is the
    PID of the current process.

    @attention: Make sure you know really well what fork(2) does before using this method

    @param stdout: Path to file to dump stdout output of daemon process to
    @type stdout: string
    @param stderr: Path to file to dump stderr output of daemon process to
    @type stderr: string
    @param chdir: Path to chdir(2) to after forking. Set to None to disable chdir'ing
    @type chdir: string or None
    @param umask: Umask to set after forking. Set to -1 not to set umask
    @type umask: number
    @param uid: UID of the user to impersonate
    @type uid: number
    @param gid: GID of the group to impersonate
    @type gid: number

    @returns: Daemon status and PID
    @rtype: tuple<bool, number>

    @raise RuntimeError: System does not support fork(2)
    '''
    #pylint: disable-msg=R0912
    if not hasattr(os, 'fork'):
        raise RuntimeError(
                'os.fork not found, daemon mode not supported on your system')

    def check_output_permissions(file_):
        '''
        Test whether the current user (which might no longer be the user
        running the parent process) is allowed to write to the requested
        output files, before performing a double fork.
        '''
        try:
            fd = os.open(file_, os.O_CREAT | os.O_WRONLY)
        except IOError, e:
            try:
                import errno
            except ImportError:
                # We can't provide a nicer error message, re-raise the original
                # exception
                # Note we can't use plain 'raise' here, since this would
                # re-raise the ImportError we're catching
                raise e

            if not hasattr(errno, 'EACCES'):
                # Same as above
                raise e

            if e.errno == errno.EACCES:
                try:
                    import pwd
                except ImportError:
                    # Same as above
                    raise e

                try:
                    user = pwd.getpwuid(os.getuid()).pw_name
                except (KeyError, AttributeError):
                    # Unknown user or no os.getuid() available or something
                    # alike
                    user = None

                if user:
                    raise RuntimeError('User %s has no permissions to open '
                                       'file \'%s\' for writing' % \
                                       (user, file_))
                else:
                    raise RuntimeError('Current user has no permissions to '
                                       'open file \'%s\' for writing' % file_)
            else:
                raise
        else:
            os.close(fd)

    if stdout:
        check_output_permissions(stdout)
    if stderr:
        check_output_permissions(stderr)
    # Output redirection should be safe once we're here

    pid = os.fork()
    if pid == 0:
        #First child
        #Become session leader...
        os.setsid()

        #Double fork
        pid = os.fork()
        if pid == 0:
            #Second child
            if umask >= 0:
                os.umask(umask)
            if chdir:
                os.chdir(chdir)
        else:
            #First child is useless now
            print 'CHILDPID=%d' % pid
            if hasattr(os, 'getuid'):
                print 'UID=%d' % os.getuid()
            if hasattr(os, 'getgid'):
                print 'GID=%d' % os.getgid()
            sys.exit()
    else:
        return False, os.getpid()

    #Close all FDs
    import resource
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if maxfd == resource.RLIM_INFINITY:
        maxfd = 1024

    sys.stdin.close()
    if not stdout:
        sys.stdout.close()
    if not stderr:
        sys.stderr.close()

    def close_safe(fd):
        '''Close a file descriptor ignoring any exception it generates'''
        #pylint: disable-msg=W0704
        try:
            os.close(fd)
        except OSError:
            pass

    close_safe(0)
    if not stdout:
        close_safe(1)
    if not stderr:
        close_safe(2)

    for fd in xrange(3, maxfd):
        close_safe(fd)

    #Open fd0 to /dev/null
    redirect = getattr(os, 'devnull', '/dev/null')
    os.open(redirect, os.O_RDWR)

    #dup to stdout and stderr
    if not stdout:
        os.dup2(0, 1)
    else:
        fd = os.open(stdout, os.O_CREAT | os.O_WRONLY)
        os.dup2(fd, 1)
        close_safe(fd)
    if not stderr:
        os.dup2(0, 2)
    else:
        fd = os.open(stderr, os.O_CREAT | os.O_WRONLY)
        os.dup2(fd, 2)
        close_safe(fd)

    return True, os.getpid()

def main():
    '''Main entry point'''
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('-d', '--daemonize', dest='daemonize',
            help='daemonize the child process', action='store_true')
    parser.add_option('-o', '--stdout', dest='stdout',
            help='file to redirect stdout output', metavar='FILE')
    parser.add_option('-e', '--stderr', dest='stderr',
            help='file to redirect stderr output', metavar='FILE')
    parser.add_option('-u', '--uid', dest='uid',
            help='UID of user to setuid() to before running the daemon ' \
                 'process', metavar='UID', type='int')
    parser.add_option('-g', '--gid', dest='gid',
            help='GID of group to setgid() to before running the daemon ' \
                 'process', metavar='GID', type='int')

    #Only parse until a '--' argument
    if not '--' in sys.argv:
        raise RuntimeError('No -- argument found')

    begin_idx = 0 if sys.argv[0] != '-c' else 1
    options, args = parser.parse_args(
        args=sys.argv[begin_idx:sys.argv.index('--')])

    if not options.daemonize and options.stdout:
        raise RuntimeError('Stdout redirection is not available in '
                           'foreground mode')
    if not options.daemonize and options.stderr:
        raise RuntimeError('Stderr redirection is not available in '
                           'foreground mode')

    if options.stdout and not os.path.isdir(os.path.dirname(options.stdout)):
        raise ValueError('Folder of stdout file does not exist')
    if options.stderr and not os.path.isdir(os.path.dirname(options.stderr)):
        raise ValueError('Folder of stderr file does not exist')

    change_uid_gid(options.uid, options.gid)

    if options.daemonize:
        daemon, _ = daemonize(options.stdout, options.stderr)

        if not daemon:
            #Give first fork time to print daemon info
            time.sleep(0.2)
            return

    # We're the daemon now, or no daemonization was requested.
    # execlp to replace ourself with the application our consumer actually
    # wants to run
    args = sys.argv[sys.argv.index('--') + 1:]

    # Reset all signal handlers
    # Check reset_signals in process.py for a more in-depth explanation
    import signal
    for i in xrange(1, signal.NSIG):
        if signal.getsignal(i) != signal.SIG_DFL:
            #pylint: disable-msg=W0704
            try:
                signal.signal(i, signal.SIG_DFL)
            except RuntimeError:
                pass

    os.execlp(args[0], *args)

if __name__ == '__main__':
    main()