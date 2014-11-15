from JumpScale import j
from .SerializerInt import SerializerInt
from .SerializerTime import SerializerTime
from .SerializerBase64 import SerializerBase64
from .SerializerHRD import SerializerHRD
from .SerializerDict import SerializerDict
from .SerializersFactory import SerializersFactory
from .SerializerBlowfish import SerializerBlowfish

j.base.loader.makeAvailable(j, 'db')

j.db.serializers=SerializersFactory()
j.db.serializers.int = SerializerInt()
j.db.serializers.time = SerializerTime()
j.db.serializers.base64 = SerializerBase64()
j.db.serializers.hrd = SerializerHRD()
j.db.serializers.dict = SerializerDict()
j.db.serializers.blowfish = SerializerBlowfish()
