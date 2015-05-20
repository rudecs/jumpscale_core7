import collections
from StringIO import StringIO


class UCISection(collections.OrderedDict):
    _option = '\toption {key} \'{value}\'\n'
    _list = '\tlist {key} \'{value}\'\n'

    def __init__(self, type, name=None, *args, **kwargs):
        super(UCISection, self).__init__(*args, **kwargs)
        self.type = type
        self.name = name

    def __cmp__(self, o):
        return cmp(str(self), str(o))

    def __str__(self):
        name = '\'%s\'' % self.name if self.name else ''
        return 'config {type} {name}'.format(
            type=self.type,
            name=name
        ).strip()

    def __repr__(self):
        return str(self)

    def dump(self, out):
        out.write(str(self) + '\n')

        for key, value in self.iteritems():
            if isinstance(value, bool):
                out.write(
                    UCISection._option.format(
                        key=key, value=int(value)
                    )
                )
            elif isinstance(value, (basestring, int, float)):
                out.write(
                    UCISection._option.format(
                        key=key, value=value
                    )
                )
            elif isinstance(value, list):
                for v in value:
                    out.write(
                        UCISection._list.format(
                            key=key, value=v
                        )
                    )
            else:
                raise ValueError('Unknow value type %s' % type(value))
        out.write('\n')

    def dumps(self):
        buffer = StringIO()
        try:
            self.dump(buffer)
            return buffer.getvalue()
        finally:
            buffer.close()


class UCI(object):
    def __init__(self, package):
        self._package = package
        self._sections = list()

    @property
    def sections(self):
        return self._sections

    @property
    def package(self):
        return self._package

    def add(self, type, name=None):
        section = UCISection(type, name)
        self._sections.append(section)
        return section

    def remove(self, section):
        self._sections.remove(section)

    def find(self, type, name=None):
        sections = []
        for section in self.sections:
            if section.type != type:
                continue
            if name is not None and section.name != name:
                continue

            sections.append(section)
        return sections

    def loads(self, ucistr):
        section = None
        for line in ucistr.split('\n'):
            line = line.strip()
            if not line:
                continue

            parts = line.split(' ', 2)
            type_, key = parts[:2]
            value = None

            if len(parts) == 3:
                value = parts[2].strip('\'')

            if type_ == 'package':
                if key != self.package:
                    raise Exception('Package name conflict')
            elif type_ == 'config':
                section = UCISection(key, value)
                self._sections.append(section)
            elif section is None:
                raise Exception('Invalid uci syntax at line: %s' % line)
            elif type_ == 'option':
                section[key] = value
            elif type_ == 'list':
                if key not in section:
                    section[key] = list()
                section[key].append(value)
            else:
                raise Exception('Unknown type: %s' % line)

    def dump(self, out):
        out.write('package %s\n\n' % self.package)

        for section in self.sections:
            section.dump(out)

    def dumps(self):
        buffer = StringIO()
        try:
            self.dump(buffer)
            return buffer.getvalue()
        finally:
            buffer.close()

    def __str__(self):
        return 'package %s' % self.package

    def __repr__(self):
        return str(self)
