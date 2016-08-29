from xml.etree import ElementTree
from JumpScale import j


class NetworkScanner:
    COMMAND = 'nmap -n --disable-arp-ping -send-ip -Pn -sS -p{ports} -oX - {cidr}'

    def __init__(self, cidr, ports=[80]):
        code, _ = j.system.process.execute('which nmap', outputToStdout=False, dieOnNonZeroExitCode=False)
        if code != 0:
            raise j.exceptions.RuntimeError('nmap is not installed')

        self._ports = ','.join([str(port) for port in ports])
        self._cidr = cidr

    def scan(self):
        """nmap -n --disable-arp-ping -send-ip -Pn -sS -p22 -oX - 172.17.0.1/24"""

        cmd = self.COMMAND.format(ports=self._ports, cidr=self._cidr)
        code, output = j.system.process.execute(cmd, outputToStdout=False, dieOnNonZeroExitCode=False)
        if code != 0:
            raise j.exceptions.RuntimeError('nmap scan failed')

        dom = ElementTree.fromstring(output)
        hosts = {}
        for host in dom.findall('host'):
            address = host.find('address').attrib['addr']
            for port in host.findall('ports/port'):
                if port.find('state').attrib['state'] == 'open':
                    hosts.setdefault(address, []).append(int(port.attrib['portid']))
        return hosts
