from JumpScale import j
import struct
import hashlib
import yaml
import json

from JSModel.serializers import YamlSerializer

class ActorObject(object):
    """
    ActorObject
    """

    _DATA_TYPE_ID = 2
    _KEY_PREFIX = 'ActorObject_'

    def __init__(self, service):
        """
        ActorObject constructor

        @param service: service the ActorObject relates to
        @type service: LocalService
        """

        self._service = service
        self.model = None
        

    def serializeToYAML(self):       
        """
        Serialize the model object to YAML 
        """ 
        return self.model.serialize(YamlSerializer)    
    
    def serializeToJSON(self):
        """
        Serialize the model object 
        """
        yaml2=self.serializeToYAML()
        objectdicts=yaml.load(yaml2)        
        #@todo P1 better code required, need to serialize directly to JSON, now too slow
        return json.dumps(objectdicts) 

    def pm_getId(self):
        """
        Retrieves the last registered id for this type of ActorObject, increments and registers it.
        """

        key = '%(prefix)s%(actorObjectName)s' % {'prefix': self._KEY_PREFIX,
                                                 'actorObjectName': self.__class__.__name__}
        retryAttempts = 5
        id = None

        if self._service.db.exists(key):
            while retryAttempts > 0:
                lastId = int(self._service.db.get(key))
                id = lastId + 1

                if self._service.db.testAndSet(key, str(lastId), str(id)) == str(lastId):
                    break

                retryAttempts -= 1

            if not id:
                raise RuntimeError('Could not get an unique id for the actor object')
        else:
            id = 1
            self._service.db.set(key, str(id))

        return id


    @classmethod
    def deserialize(cls, data, service):
        """
        Deserializes an ActorObject instance

        @return: deserialized ActorObject instance
        @rtype: ActorObject
        """

        dataTypeId = struct.unpack('B', data[0])[0]

        if dataTypeId != cls._DATA_TYPE_ID:
            raise RuntimeError('Could not deserialize data, unknown dataTypeId: %(dataTypeId)s' % {'dataTypeId':dataTypeId})

        dataHash = hashlib.md5(data[:-16]).digest()

        if dataHash != data[-16:]:
            raise RuntimeError('Could not deserialize data, incorrect data hash')

        actorObjectTypeLen = struct.unpack('B', data[1])[0]

        actorObjectType = data[2:actorObjectTypeLen + 2]
        actorObjectManagerType = '%(actorObjectType)smanager' % {'actorObjectType': actorObjectType.lower()}
        actorObjectManager = getattr(service.extensions, actorObjectManagerType)
        actorObject = actorObjectManager.get()

        serializedModel = data[actorObjectTypeLen + 2:-16]
        actorObject.model = actorObject.model.deserialize(j.db.JSModelserializers.thriftbase64, serializedModel)
        return actorObject


    def serialize(self):
        """
        Serializes an ActorObject instance.

        @return: serialized ActorObject instance
        @rtype: String
        """

        actorObjectType = self.__class__.__name__
        serializedModel = self.model.serialize(j.db.JSModelserializers.thriftbase64)

        data = struct.pack('B', self._DATA_TYPE_ID)
        data += struct.pack('B', len(actorObjectType))
        data += actorObjectType
        data += serializedModel
        data += hashlib.md5(data).digest()

        return data


    def __repr__(self):
        return str(self.model)
