from JumpScale import j
try:
    import ujson as json
except:
    import json

import JumpScale.baselib.hash
# import JumpScale.grid.osis
# import JumpScale.baselib.redis

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()
# import time
# import inspect

class Job(OsisBaseObject):

    """
    identifies a job in the grid
    """

    def __init__(self, ddict={}):
        if ddict <> {}:
            self.load(ddict)
        else:
            self.guid=0  #WE WILL NO LONGER USE ID's
            # self.sessionid = sessionid
            self.gid =j.application.whoAmI.gid
            self.nid =j.application.whoAmI.nid

            self.js_org=""
            self.js_actor=""
            self.js_name=""
            self.js_action=""
            self.js_version=0            

            self.args=args

            self.timeout=timeout

            self.parent=None

            self.resultcode=None
            self.result=None

            self.state="SCHEDULED" #SCHEDULED,STARTED,ERROR,OK,NOWORK

            self.timeStart=j.base.time.getTimeEpoch()
            self.timeStop=0


    def setArgs(self,action):
        import inspect
        args = inspect.getargspec(action)
            # args.args.remove("session")
            # methods[name] = {'args' : args, 'doc': inspect.getdoc(method)}
        self.args = args.args
        self.argsDefaults = args.defaults
        self.argsVarArgs = args.varargs
        self.argsKeywords = args.keywords
        source=inspect.getsource(action)
        splitted=source.split("\n")
        splitted[0]=splitted[0].replace(action.func_name,"action")
        self.source="\n".join(splitted)
            
    # def getSetGuid(self):
    #     """
    #     use osis to define & set unique guid (sometimes also id)
    #     """
    #     self.gid = int(self.gid)
    #     self.id = int(self.id)
    #     self.guid = j.base.byteprocessor.hashTiger160(self.getContentKey())  # need to make sure roles & source cannot be changed

    #     return self.guid

    def toJson(self):
        return json.dumps(self.__dict__)


    def getContentKey(self):
        """
        is like returning the hash, is used to see if object changed
        """
        # out=""
        # for item in ["cmd","category","args","source"]:
        #     out+=str(self.__dict__[item])
        return j.tools.hash.md5_string(str(self.__dict__))

