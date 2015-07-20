from JumpScale import j
import JumpScale.baselib.serializers
from JumpScale.grid.serverbase import returnCodes
from JumpScale.core.errorhandling.ErrorConditionHandler import BaseException
import inspect
import copy
import time
import ujson


class Session():

    def __init__(self, ddict):
        self.__dict__ = ddict

        if not hasattr(self, 'nid'):
            self.nid = None

    def __repr__(self):
        return str(self.__dict__)

    def updateNodeId(self, new_node_id):
        """
        Sets the session's NID attribute to the provided new_node_id.
        """
        self.nid = new_node_id

    __str__ = __repr__


class DaemonCMDS(object):

    def __init__(self, daemon):
        self.daemon = daemon

    def authenticate(self, session):
        return True  # will authenticall all (is std)

    def registerpubkey(self, organization, user, pubkey, session):
        self.daemon.keystor.setPubKey(organization, user, pubkey)
        return ""

    def listCategories(self, session):
        return list(self.daemon.cmdsInterfaces.keys())

    def getpubkeyserver(self, session):
        return self.daemon.keystor.getPubKey(self.daemon.sslorg, self.daemon.ssluser, returnAsString=True)

    def registersession(self, sessiondata, ssl,session):
        """
        @param sessiondata is encrypted data (SSL)
        """
        # ser=j.db.serializers.getMessagePack()
        # sessiondictstr=ser.loads(data)
        print("register session:%s "%session)
        # for k, v in list(sessiondata.items()):
        #     if isinstance(k, bytes):
        #         sessiondata.pop(k)
        #         k = k.decode('utf-8', 'ignore')
        #     if isinstance(v, bytes):
        #         v = v.decode('utf-8', 'ignore')
        #     sessiondata[k] = v
        session = Session(sessiondata)

        if ssl:
            session.encrkey = self.daemon.decrypt(session.encrkey, session)
            session.passwd = self.daemon.decrypt(session.passwd, session)

        if not self.authenticate(session):
            raise RuntimeError("Cannot Authenticate User:%s" % session.user)
        self.daemon.sessions[session.id] = session
        print("OK")

        return "OK"

    def logeco(self, eco, session):
        """
        log eco object (as dict)
        """
        eco["epoch"] = self.daemon.now
        eco = j.errorconditionhandler.getErrorConditionObject(ddict=eco)
        self.daemon.eventhandlingTE.executeV2(eco=eco, history=self.daemon.eventsMemLog)

    def introspect(self, cat,session=None):
        methods = {}
        interface = self.daemon.cmdsInterfaces[cat]
        for name, method in inspect.getmembers(interface, inspect.ismethod):
            if name.startswith('_'):
                continue
            args = inspect.getargspec(method)
            # Remove the 'session' parameter
            if 'session' in args.args:
                session_index = args.args.index('session')
                if session_index!=len(args.args)-1:
                    raise RuntimeError("session arg needs to be last argument of method. Cat:%s Method:%s \nArgs:%s"%(cat,name,args))
                del args.args[session_index]
                if args.defaults:
                    session_default_index = session_index - len(args.args) - 1
                    defaults = list(args.defaults)
                    del defaults[session_default_index]
                    args = inspect.ArgSpec(args.args, args.varargs, args.keywords, defaults)

            methods[name] = {'args': args, 'doc': inspect.getdoc(method)}
        return methods


class Daemon(object):

    def __init__(self, name=None):
        j.application.interactive = False # make sure errorhandler does not require input we are daemon
        self.name = name
        self._command_handlers = {}     # A cache used by command_handler()
        self.cmds = {}
        self.cmdsInterfaces = {}
        self.cmdsInterfacesProxy = {}
        self._now = 0
        self.sessions = {}
        self.key = ""
        self.errorconditionserializer = j.db.serializers.getSerializerType("m")
        self.addCMDsInterface(DaemonCMDS, "core")

    def getTime(self):
        # can overrule this to e.g. in gevent set the time every sec, takes less resource (using self._now)
        return int(time.time())

    def decrypt(self, message, session):
        if session.encrkey:
            return self.keystor.decrypt(orgsender=session.organization, sender=session.user,
                                        orgreader=self.sslorg, reader=self.ssluser,
                                        message=message[0], signature=message[1])
        else:
            return message

    def notifyOfNewNode(self, node, session_id):
        """
        Notifies this daemon about a newly-registered node.

        Args:
            node: metadata about the new node.
            session_id (str): the ID of the session the new node is involved in.
        """
        if hasattr(node, 'id'):
            # Let's use this opportunity to update the associated session with the new NID
            self.sessions[session_id].updateNodeId(node.id)

    def encrypt(self, message, session):
        if session and session.encrkey:
            if not hasattr(session, 'publickey'):
                session.publickey = self.keystor.getPubKey(user=session.user, organization=session.organization, returnAsString=True)
            return self.keystor.encrypt(self.sslorg, self.ssluser, "", "", message, False, pubkeyReader=session.publickey)[0]
        else:
            return message

    def addCMDsInterface(self, cmdInterfaceClass, category,proxy=False):
        if category not in self.cmdsInterfaces:
            self.cmdsInterfaces[category] = []
        if proxy==False:
            obj=cmdInterfaceClass(self)
        else:
            obj=cmdInterfaceClass()
            self.cmdsInterfacesProxy[category]=obj
        self.cmdsInterfaces[category]=obj

    def command_handler(self, command_category, command):
        """
        Looks up the callable function responsible for handling the specified command.

        Returns:
            A callable function or None if the method could not be found.
        """
        cache_key = "%s_%s" % (command_category, command)

        if cache_key not in self._command_handlers:
            command_interface = self.cmdsInterfaces.get(command_category, None)
            self._command_handlers[cache_key] = getattr(command_interface, command, None)

        return self._command_handlers.get(cache_key, None)


    def processRPC(self, cmd, data, returnformat, session, category=""):
        """

        @return (resultcode,returnformat,result)
                item 0=cmd, item 1=returnformat (str), item 2=args (dict)
        resultcode
            0=ok
            1= not authenticated
            2= method not found
            2+ any other error
        """

        inputisdict = isinstance(data, dict)

        ffunction = self.command_handler(command_category=category, command=cmd)
        if not ffunction:
            return returnCodes.METHOD_NOT_FOUND, returnformat, ''

        try:
            if inputisdict:
                # for k, v in list(data.items()):
                #     if isinstance(k, bytes):
                #         data.pop(k)
                #         k = k.decode('utf-8', 'ignore')
                #     if isinstance(v, bytes):
                #         v = v.decode('utf-8', 'ignore')
                #     data[k] = v

                if "_agentid" in data:
                    if data["_agentid"]!=0:
                        cmds=self.cmdsInterfaces["agent"]
                        gid=j.application.whoAmI.gid
                        nid=int(data["_agentid"])
                        data.pop("_agentid")
                        category2=category.replace("processmanager_","")
                        scriptid="%s_%s" % (category2, cmd)
                        job=cmds.scheduleCmd(gid,nid,cmdcategory=category2,jscriptid=scriptid,cmdname=cmd,args=data,queue="internal",log=False,timeout=60,roles=[],session=session,wait=True)
                        jobqueue = cmds._getJobQueue(job["guid"])
                        jobr=jobqueue.get(True,60)
                        if not jobr:
                            eco = j.errorconditionhandler.getErrorConditionObject(msg="Command %s.%s with args: %s timeout" % (category2, cmd, data))
                            return returnCodes.ERROR,returnformat,eco.__dict__
                        jobr=ujson.loads(jobr)
                        if jobr["state"]!="OK":
                            return jobr["resultcode"],returnformat,jobr["result"]
                        else:
                            return returnCodes.OK,returnformat,jobr["result"]
                    else:

                        data.pop("_agentid")
                data['session'] = session
                result = ffunction(**data)
            else:
                result = ffunction(data, session=session)
        except Exception as e:
            if isinstance(e, BaseException):
                return returnCodes.ERROR, returnformat, e.eco
            eco = j.errorconditionhandler.parsePythonErrorObject(e)
            eco.level = 2
            eco.data = data
            # print eco
            # eco.errormessage += "\nfunction arguments were:%s\n" % str(inspect.getargspec(ffunction).args)
            data.pop('session', None)
            if len(str(data))>1024:
                data="too much data to show."


            eco.errormessage = \
                "ERROR IN RPC CALL %s: %s. (Session:%s)\nData:%s\n" % (cmd, eco.errormessage, session, data)

            eco.process()
            eco.__dict__.pop("tb", None)
            eco.tb=None
            errorres = eco.__dict__
            return returnCodes.ERROR, returnformat, errorres 

        return returnCodes.OK, returnformat, result


    def getSession(self, cmd, sessionid):
        if sessionid in self.sessions:
            session = self.sessions[sessionid]
        else:
            # if isinstance(cmd, bytes):
            #     cmd = cmd.decode('utf-8', 'ignore')
            if cmd in ["registerpubkey", "getpubkeyserver", "registersession"]:
                session = None
            else:
                error = "Authentication  or Session error, session not known with id:%s" % sessionid
                eco = j.errorconditionhandler.getErrorConditionObject(msg=error)
                return returnCodes.AUTHERROR, "m", self.errorconditionserializer.dumps(eco.__dict__)
        return session

    def processRPCUnSerialized(self, cmd, informat, returnformat, data, sessionid, category=""):
        """
        @return (resultcode,returnformat,result)
                item 0=cmd, item 1=returnformat (str), item 2=args (dict)
        resultcode
            0=ok
            1= not authenticated
            2= method not found
            2+ any other error
        """
        session = self.getSession(cmd, sessionid)
        if isinstance(session, tuple):
            return session
        try:
            if informat != "":
                # if isinstance(informat, bytes):
                #     informat = informat.decode('utf-8', 'ignore')
                ser = j.db.serializers.get(informat, key=self.key)
                data = ser.loads(data)
        except Exception as e:
            eco=j.errorconditionhandler.parsePythonErrorObject(e)
            eco.tb=""
            return returnCodes.SERIALIZATIONERRORIN, "m", self.errorconditionserializer.dumps(eco.__dict__)

        parts = self.processRPC(cmd, data, returnformat=returnformat, session=session, category=category)
        returnformat = parts[1]  # return format as comes back from processRPC
        # if isinstance(returnformat, bytes):
        #     returnformat = returnformat.decode('utf-8', 'ignore')
        if returnformat != "":  # is
            returnser = j.db.serializers.get(returnformat, key=session.encrkey)
            error=0
            try:
                data = self.encrypt(returnser.dumps(parts[2]), session)
            except Exception as e:
                error=1
            if error==1:
                try:
                    data = self.encrypt(returnser.dumps(parts[2].__dict__), session)
                except:
                    eco = j.errorconditionhandler.getErrorConditionObject(msg="could not serialize result from %s"%cmd)
                    return returnCodes.SERIALIZATIONERROROUT, "m", self.errorconditionserializer.dumps(eco.__dict__)
        else:
            data = parts[2]

        if data == None:
            data = ""

        return (parts[0], parts[1], data)
