from .ActorObject import ActorObject 

class ActorObjects:
	"""
	class that provides streaming of ActorObjects from and to a bytestream.
	Because ActorObject names are only unique within the scope of a service
	this class will need a service reference. 
	"""
	def __init__(self,service):
		"""
		@param service 	reference to the service that will contain this object 
		"""
		self._service = service 

	def readFromByteStream(self,byteStream):
		"""
		return a ActorObject 
		"""
		return ActorObject.deserialize(byteStream,self._service)
		

	def writeToByteStream(self,actorObject):
		"""
		write an actorObject to a stream 
		"""
		return actorObject.serialize()