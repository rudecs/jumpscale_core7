import functools


class BaseService(object):
    def __init__(self, wrt):
        self._wrt = wrt
        self._package = None

    @property
    def package(self):
        if self._package is None:
            self._package = self._wrt.get(self.PACKAGE)

        return self._package


class BaseServiceSection(object):
    def __new__(cls, *args, **kwargs):
        exposed_fields = cls.EXPOSED_FIELDS \
            if hasattr(cls, 'EXPOSED_FIELDS') else []

        for field in exposed_fields:
            prop = property(
                functools.partial(cls._get, field=field),
                functools.partial(cls._set, field=field)
            )

            setattr(cls, field, prop)

        exposed_bool_fields = cls.EXPOSED_BOOLEAN_FIELDS \
            if hasattr(cls, 'EXPOSED_BOOLEAN_FIELDS') else []

        for field in exposed_bool_fields:
            prop = property(
                functools.partial(cls._getb, field=field),
                functools.partial(cls._set, field=field)
            )
            setattr(cls, field, prop)

        return super(BaseServiceSection, cls).__new__(cls, *args, **kwargs)

    def _get(self, field):
        return self.section.get(field)

    def _getb(self, field):
        return self.section.getBool(field, True)

    def _set(self, value, field):
        self.section[field] = value

    def __init__(self, section):
        self._section = section

    @property
    def section(self):
        return self._section
