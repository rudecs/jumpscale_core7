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

    def send_message(self,msg,feedback=False,markup=None):
        # print "spawn:%s"%msg
        self.tg.send_message(self.chatid,msg, reply_to_message_id="",reply_markup=self._processmarkup(markup))
        if feedback:
            self.event=Event()   
            self.event.wait()     
            return self.returnmsg.text     

    def start_communication(self):
        self._activate()
        self.handler.activeCommunications[self.user]=self

    def stop_communication(self):
        self.handler.activeCommunications.pop(self.user)

class InteractiveHandler:

    def __init__(self):
        self.once = []
        self.sessions = {}
        self.activeCommunications = {}
        self.activeSessions = {}
        self.actions={}
        self.lastactionshash=""

    def checkSession(self,tg,message,name="main",newcom=True):
        username=message.from_user.username
        key="%s_%s"%(username,name)
        if not self.sessions.has_key(key):
            self.sessions[key]=Session(self,tg,message.chat.id,username,name)
        if newcom:
            self.sessions[key].start_communication()        
        return self.sessions[key]

    def checkFirst(self,message):
        username=message.from_user.username
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
        
    def on_text(self, tg, message):
        print "recv:%s"%message.text
        username=message.from_user.username
        if self.activeCommunications.has_key(username):
            #returning message from flow
            session=self.activeCommunications[username]
            session.returnmsg=message
            if session.event!=None:
                session.event.set()
                print "event release"
                return


        if self.checkFirst(message):
            print tg.send_message(message.chat.id, "Welcome to the demo bot,send '?' for help.")
            # print tg.send_message(message.chat.id, help)
            # print "send init photo"
            # print tg.send_photo(message.chat.id, self.image,reply_to_message_id="", reply_markup="")
            # print "photo send"
            self.once.append(username)

        text=message.text.strip()

        if text=="?":       
            h="Available actions (call them with '!$actionname')\n"
            for key,action in self.actions.iteritems():
                h+="- '%-20s' : %s\n"%(key, action.description)                    
            h+="If you need more help on 1 action, do '!$actionname?'\n"
            h+="If you do ?? you get more info about the robot system."
            print tg.send_message(message.chat.id, h)            

        if text.startswith("!"):
            cmd=text.strip("?!")
            if cmd in self.actions.keys():
                if text[-1]=="?":                        
                    h="Help for %s:\n"%cmd
                    h+=self.actions[cmd].help+"\n"
                    print tg.send_message(message.chat.id, h)            
                else:
                    gevent.spawn(self.actions[cmd].action,self,tg,message)


    def maintenance(self):
        lasthash=j.tools.hash.md5_string(str( j.tools.hash.hashDir("actions")))
        if lasthash!=self.lastactionshash:
            print "load actions"
            self.actions={}
            for path in j.system.fs.listFilesInDir("actions",recursive=True,filter="*.py"):
                name=j.system.fs.getBaseName(path)[:-3]
                mod = imp.load_source(name, path)
                self.actions[name]=mod
            self.lastactionshash=lasthash
