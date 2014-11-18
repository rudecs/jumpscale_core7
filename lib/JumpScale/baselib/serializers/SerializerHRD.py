from JumpScale import j
import uuid
from JumpScale.core.system.text import Text

class SerializerHRD():
    def __init__(self):
        self._primitiveTypes = (int, str, float, bool)
        self.__escape = str(uuid.uuid1())

    def _formatPrepends(self, prepend, type):
        prepend = prepend+'.' if prepend and prepend[-1] != '.' else prepend
        return '%s = %s\n' % (prepend, type)

    def dumps(self, data, prepend=''):
        if data == None:
            return self._formatPrepends(prepend, 'None')
        if isinstance(data, dict):
            processed = self._dumpDict(data, prepend)
        elif isinstance(data, list):
            processed = self._dumpList(data, prepend)
        else:
            processed = data
            if not isinstance(data, str):
                processed = '%s.' % data
        return processed

    def _dumpDict(self, dictdata, prepend=''):
        dictified = ''
        if not dictdata:
            dictified += self._formatPrepends(prepend, '{}')
        for k, v in dictdata.items():
            if isinstance(k, str) and '..' in k:
                k = k.replace('..', self.__escape)
            if not (isinstance(v, self._primitiveTypes)):
                v = self.dumps(v, '%s%s.' % (prepend,k))
                dictified += v
            else:
                k = k.replace(self.__escape, '..')
                if not isinstance(v, str):
                    dictified += '%s%s. = %s\n' % (prepend, k, v)
                else:
                    dictified += '%s%s = %s\n' % (prepend, k, v)
        return dictified

    def _dumpList(self, listdata, prepend=''):
        listified = ''
        if not listdata:
            listified += self._formatPrepends(prepend, '[]')
        for index, item in enumerate(listdata):
            if prepend:
                listprepend = '%s[%s].' % (prepend, index)
            else:
                listprepend = '[%s].' % index
            if not (isinstance(item, self._primitiveTypes)):
                item = self.dumps(item, listprepend)
                listified += '%s' % item
            else:
                if not isinstance(item, str):
                    listified += '%s. = %s\n' % (listprepend[:-1], item)
                else:
                    listified += '%s = %s\n' % (listprepend[:-1], item)
        return listified



    def loads(self, data):
        dataresult = [] if data.startswith('[') else {}
        for line in data.splitlines():
            if '=' not in line:
                if line.endswith('.'):
                    return self._getType(line[:-1])
                return line
            key, value = line.split('=')
            key = key.replace('..', self.__escape)
            dataresult = self._processKey(key.strip(), value.strip(), dataresult)
        return dataresult

    def _processKey(self, key, value, result):
        if result == None:
            result = [] if key.startswith('[') else {}
        if key.endswith('.'):
            key = key[:-1]
            value = self._getType(value)

        if key.find('.') == -1:
            key = key.replace(self.__escape, '..')
            if key.startswith('['):
                index = int(key[1:-1])
                result.insert(index, value)
            else:
                result[key] = value
        else:
            keypart, keyrest = key.split('.', 1)
            if keypart.startswith('['):
                index = int(keypart[1:-1])
                if len(result) <= index:
                    result.append(None)
                value = self._processKey(keyrest, value, result[index])
                result[index] = value
            else:
                if not keypart in result:
                    result[keypart] = None
                value = self._processKey(keyrest, value, result[keypart])
                result[keypart] = value
        return result

    def _getType(self, value):
        values = {'{}': {}, '[]': [], 'None': None}
        if value in values:
            return values[value]
        elif j.basetype.integer.checkString(value):
            primitive = j.basetype.integer.fromString(value)
        elif j.basetype.float.checkString(value):
            primitive = j.basetype.float.fromString(value)
        elif j.basetype.boolean.checkString(value):
            primitive = j.basetype.boolean.fromString(value)
        else:
            j.basetype.string.fromString(value)
        return primitive