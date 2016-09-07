from JumpScale import j

CMD = "tap-ctl"


class TAPCTL(object):
    def list(self):
        rc, output = j.system.process.execute("{} list".format(CMD))
        devices = {}
        for line in output.splitlines():
            parts = line.split()
            device = {}
            for part in parts:
                key, value = part.split('=')
                device[key] = value
            device['dev'] = '/dev/blktap{}'.format(device['minor'])
            devices[device['minor']] = device
        return devices

    def create(self, filename):
        rc, output = j.system.process.execute("{} create -a {}".format(CMD, filename))
        if rc == 0:
            return output
        raise ValueError("Failed to create tap device {}".format(output))
