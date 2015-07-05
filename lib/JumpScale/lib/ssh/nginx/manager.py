from JumpScale import j


class NginxManagerFactory(object):
    def get(self, con, path='/etc/nginx/nginx.conf'):
        return NginxManager(con, path)


class NginxManager(object):
    def __init__(self, con=None, path='/etc/nginx/nginx.conf'):
        if con is None:
            con = j.ssh.connection

        self._path = path
        self._con = con
        self._config = None

    def start(self):
        self._con.upstart_ensure('nginx')

    def stop(self):
        self._con.upstart_stop('nginx')

    def restart(self):
        self._con.upstart_restart('nginx')

    def reload(self):
        self._con.upstart_reload('nginx')

    @property
    def config(self):
        if self._config is None:
            try:
                content = self._con.file_read(self._path)
            except AssertionError:
                # file does not exit
                content = ''
            self._config = NginxConfig(content.strip())
        return self._config

    def commit(self):
        self._con.file_write(self._path, self.config.content)


class NginxBaseConfig(object):
    def __init__(self, config):
        self._properties = list()
        for key, value in config:
            if isinstance(value, basestring):
                self._properties.append([key, value])
            else:
                self._specialconfig(key, value)

    @property
    def properties(self):
        return self._properties

    def addProperty(self, directive, value):
        self._properties.append((directive, value))


class NginxConfig(NginxBaseConfig):
    def __init__(self, content):
        self.http = None
        self.events = None
        import nginxparser
        if content:
            config = nginxparser.loads(content)
        else:
            config = []
        super(NginxConfig, self).__init__(config)
        if self.http is None:
            self.http = NginxHTTP([])
        if self.events is None:
            self.events = NginxEvents([])

    def _specialconfig(self, key, value):
        if key[0] == 'http':
            self.http = NginxHTTP(value)
        elif key[0] == 'events':
            self.events = NginxEvents(value)

    @property
    def content(self):
        import jinja2
        import os
        jinja = jinja2.Environment(
            trim_blocks=True,
            variable_start_string="${",
            variable_end_string="}",
            loader=jinja2.FileSystemLoader(
                os.path.join(os.path.dirname(__file__), 'templates')
            )
        )

        template = jinja.get_template('nginxJinjaTemplate')
        content = template.render(properties=self.properties,
                                  events=self.events.properties,
                                  http=self.http,
                                  servers=self.http.servers)
        return content


class NginxEvents(NginxBaseConfig):
    pass


class NginxHTTP(NginxBaseConfig):
    def __init__(self, config):
        self.servers = list()
        super(NginxHTTP, self).__init__(config)

    def _specialconfig(self, key, value):
        if key[0] == 'server':
            self.servers.append(NginxServer(value))

    def addServer(self):
        server = NginxServer([])
        self.servers.append(server)
        return server


class NginxServer(NginxBaseConfig):
    def __init__(self, config):
        self.locations = list()
        super(NginxServer, self).__init__(config)

    def _specialconfig(self, key, value):
        if key[0] == 'location':
            self.locations.append(NginxLocation(key[1], value))

    def addLocation(self, path):
        location = NginxLocation(path, [])
        self.locations.append(location)
        return location


class NginxLocation(NginxBaseConfig):
    def __init__(self, path, config):
        self.path = path
        super(NginxLocation, self).__init__(config)
