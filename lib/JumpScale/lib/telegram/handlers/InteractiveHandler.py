from datetime import datetime
import gevent
import json
from JumpScale import j
import json

import imp

import gevent
from gevent.event import Event

help="""
build in commands:
- !session.args
- !session.list
- !session.switch
- !session.kill
- !session.status

"""


class Session:
    def __init__(self,handler,tg,chatid,user,name):
        self.handler=handler
        self.tg = tg
        self.name = name
        self.user=user
        self.chatid=chatid
        self.event=None
        self.returnmsg=None

    def _activate(self):
        self.handler.activeSessions[self.user]=self

    def _processmarkup(self,markup):
        if markup!=None:
            markup2={}
            markup2["resize_keyboard"]=True
            markup2["one_time_keyboard"]=True 
            markup2["keyboard"]=markup
            return json.dumps(markup2)
        return markup

    def getArgument(self,key,descr="",global_=False,markup=None,presetvalue=None):
        if global_:
            hkey="config"
        else:
            hkey=self.name
        res=self.handler.redisconfig.hget(hkey,key)
        if res==None:
            # if descr=="":
            #     session.send_message("Cannot find global variable: '%s' please define by using '%s=yourinput'."%(key,key))
            # else:
            if presetvalue!=None:
                res=presetvalue
            elif descr=="":
                res=self.send_message("Cannot find variable: '%s', please specify"%key,True,markup=markup)
            else:
                # self.send_message("Cannot find global variable: '%s', please specify"%key)
                res=self.send_message(descr,True,markup=markup)
            self.handler.redisconfig.hset(hkey,key,res)
        return res

    def send_message(self,msg,feedback=False,markup=None):
        # print "spawn:%s"%msg
        self.tg.send_message(self.chatid,msg, reply_to_message_id="",reply_markup=self._processmarkup(markup))
        if feedback:
            self.start_communication()
            self.event=Event()   
            self.event.wait()     
            return self.returnmsg.text     

    def start_communication(self):
        self._activate()
        self.handler.activeCommunications[self.user]=self

    def stop_communication(self):
        if self.handler.activeCommunications.has_key(self.user):
            self.handler.activeCommunications.pop(self.user)

class InteractiveHandler:

    def __init__(self):
        self.once = []
        self.sessions = {}
        self.activeCommunications = {}
        self.activeSessions = {}
        self.actions={}
        self.lastactionshash=""

        print "connect to redis config on %s:9000"%"127.0.0.1"
        self.redisconfig=j.clients.redis.getGeventRedisClient("127.0.0.1",9000)
        print "redis connection ok"        

    def checkSession(self,tg,message,name="main",newcom=True):
        # username=message.from_user.username
        username=self.getUserName(message)
        key="%s_%s"%(username,name)
        if not self.sessions.has_key(key):
            self.sessions[key]=Session(self,tg,message.chat.id,username,name)
            self.sessions[key].send_message("Now in session:%s"%name)
        self.activeSessions[username]=self.sessions[key]
        if newcom:
            self.sessions[key].start_communication()
        self.redisconfig.hset("sessions_%s"%username,name,message.chat.id)   
        self.redisconfig.hset("sessions_active",username,name) 
        return self.sessions[key]

    def stopSession(self,tg,message,name):
        # username=message.from_user.username
        username=self.getUserName(message)
        key="%s_%s"%(username,name)
        if self.sessions.has_key(key):
            session=self.sessions[key]
            session.stop_communication()
            self.sessions.pop(key)


    def checkFirst(self,message):
        # username=message.from_user.username
        username=self.getUserName(message)
        if username in self.once:
            return False
        else:
            return True

    def test_define(self,tg,message):
        print "test.define"
        markup={}

        session=self.checkSession(tg,message,name="test",newcom=True)      
        result=int(session.send_message("Please specify how many VNAS'es you would like to use (1-10).",True))
        for i in range(result):
            session.send_message(str(i))
        markup=[["Yes"],["No"]]
        result=session.send_message("Do you want custom settings?",True,markup=markup)
        session.stop_communication()
    
    def getUserName(self,message):
        try:
            username=message.from_user.username
        except Exception,e:
            # username=message.from_user.id
            username=message.from_user.last_name+" "+message.from_user.first_name
            username=username.replace(" ","_").strip().lower()
        return username

    def on_text(self, tg, message):


        def help():
            h="Available actions (call them with '!$actionname')\n"
            for key,action in self.actions.iteritems():
                if hasattr(action,"description"):
                    h+="- '%-20s' : %s\n"%(key, action.description)                    
                else:
                    h+="- '%-20s'\n"%(key)                    
            h+="If you need more help on 1 action, do '!$actionname?'\n"
            h+="If you do ?? you get more info about the robot system.\n"
            h+="!s go to session (std session=main), without arg prints session we are in.\n"
            h+="!l lists sessions, l lists args\n"
            h+="!d aname :deletes a session with name aname\n"
            h+="@somearg=aval\n sets a global argument"
            h+="somearg=aval\n sets a session argument"

            return h

        print "recv:%s"%message.text

        username=self.getUserName(message)
            
        if self.redisconfig.hexists("sessions_active",username):
            sessionName=self.redisconfig.hget("sessions_active",username)
            session=self.checkSession(tg,message,name=sessionName,newcom=False)
        else:
            session=self.checkSession(tg,message,name="main",newcom=False)
        
        if self.activeCommunications.has_key(username):
            #returning message from flow
            session=self.activeCommunications[username]
            session.returnmsg=message
            if session.event!=None:
                session.event.set()
                print "event release"
                return

        if self.checkFirst(message):
            print tg.send_message(message.chat.id, "Send '?' for help.")
            self.once.append(username)

        text=message.text.strip()

        if text=="?":       
            print tg.send_message(message.chat.id, help())    
            return        

        if text.startswith("!list") or text=="!l":
            msg="Sessions:\n"            
            if self.redisconfig.hkeys("sessions_%s"%username)!=None:
                for item in self.redisconfig.hkeys("sessions_%s"%username):
                    msg+="- %s\n"%item
            else:
                msg="No Sessions Yet"
            tg.send_message(message.chat.id,msg)
            return

        if text.lower().startswith("!s "):
            sessionname0=text.split(" ")[1].strip()
            session=self.checkSession(tg,message,name=sessionname0,newcom=False)   
            self.activeSessions[username]=session
            return

        if text.lower()=="!s":
            session.send_message("Current Session:'%s'"%session.name)
            return

        if text.lower().startswith("!d "):
            sessionname0=text.split(" ")[1].strip()
            session=self.stopSession(tg,message,name=sessionname0)
            return

        if text=="l" or text =="@l":
            out=""
            res=self.redisconfig.hkeys("config")
            if res!=None:
                out+="Global Arguments:\n"
                for item in res:
                    val=self.redisconfig.hget("config",item)
                    out+="%-20s = %s\n"%(item,val)
            if out!="":
                out+="\n"

            res=self.redisconfig.hkeys(session.name)
            if res!=None:
                out+="Session '%s' Arguments:\n"%session.name
                for item in res:
                    val=self.redisconfig.hget(session.name,item)
                    out+="%-20s = %s\n"%(item,val)

            session.send_message(out)
            return

        if text.startswith("!"):
            cmd=text.strip("?!")
            if cmd in self.actions.keys():
                if text[-1]=="?":                        
                    h="Help for %s:\n"%cmd
                    h+=self.actions[cmd].help+"\n"
                    print tg.send_message(message.chat.id, h)            
                else:
                    try:
                        gevent.spawn(self.actions[cmd].action,session,message)
                    except Exception,e:
                        tg.send_message(message.chat.id, "could not execute, error:")
                        tg.send_message(message.chat.id, str(e))
            else:
                tg.send_message(message.chat.id, "could not find cmd")
                tg.send_message(message.chat.id, help())
                return

        if text.find("=")!=-1:
            if text[0]=="@":
                #global arg
                paramname,val=text.strip("@").split("=")
                paramname=paramname.strip()
                val=val.strip()
                self.redisconfig.hset("config",paramname,val)
                tg.send_message(message.chat.id,"global arg: '%s'='%s'"%(paramname,val))
            else:
                if self.activeSessions.has_key(username):
                    session=self.activeSessions[username]
                else:
                    #create new session
                    raise RuntimeError("there should always be a session")
                paramname,val=text.split("=")
                paramname=paramname.strip()
                val=val.strip()
                self.redisconfig.hset(session.name,paramname,val)
                tg.send_message(message.chat.id,"session arg: '%s'='%s'"%(paramname,val))
            return



    def maintenance(self):
        print "1"
        lasthash=j.tools.hash.md5_string(str( j.tools.hash.hashDir("actions")))
        if lasthash!=self.lastactionshash:
            print "load actions"
            self.actions={}
            for path in j.system.fs.listFilesInDir("actions",recursive=True,filter="*.py"):
                name=j.system.fs.getBaseName(path)[:-3]
                if name[0]!="_":
                    mod = imp.load_source(name, path)
                    self.actions[name]=mod
            self.lastactionshash=lasthash

