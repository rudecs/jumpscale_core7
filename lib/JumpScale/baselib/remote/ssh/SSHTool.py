

class SSHTool:

    def getSSHClient(self,password,  host="localhost", username="root", port=22,timeout=10):
        '''Create a new SSHClient instance.

        @param host: Hostname to connect to
        @type host: string
        @param username: Username to connect as
        @type username: string
        @param password: Password to authenticate with
        @type password: string
        @param timeout: Connection timeout
        @type timeout: number

        @return: SSHClient instance
        @rtype: SSHClient
        '''

        from SSHClient import SSHClient
        return SSHClient(host=host, port=port, username=username, password=password, timeout=timeout)

    def getSSHClientUsingKey(self,keypath,host="localhost",username="root",port=22,timeout=10):
        '''Create a new SSHClient instance.
        @return: SSHClient instance
        @rtype: SSHClient
        '''
        from SSHClient import SSHClient
        return SSHClient(host=host, port=port,keypath=keypath,username=username, timeout=timeout)

    def getSSHClientUsingSSHAgent(self,host="localhost",username="root",port=22,timeout=10):
        '''
        Create a new SSHClient instance using ssh agent.
        '''
        from SSHClient import SSHClient
        return SSHClient(host=host, port=port,username=username, timeout=timeout)        