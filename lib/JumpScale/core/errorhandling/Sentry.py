def Sentry():
    
    def sendEcoToSentry(self, eco, modulename=None, hrdprefix='sentry'):
        extra={}
        tb=eco.tb

        if eco.__dict__.has_key("frames"):
            frames=eco.frames
        else:
            frames=[]
        if eco.backtrace<>"":
            extra["tb"]=eco.backtrace

        if eco.backtraceDetailed<>"":
            extra["tb_detail"]=eco.backtraceDetailed

        if hasattr(eco,"extra") and eco.extra<>None:
            extra["details"]=eco.extra

        extra["category"]=eco.category        
        self.sendMessageToSentry(modulename=modulename,message=eco.errormessage,ttype=ttype,frames=frames,tags=None,\
            extra=extra,level=level,tb=tb, hrdprefix=hrdprefix)

    def sendMessageToSentry(self,modulename,message,ttype="bug",tags=None,extra={},level="error",tb=None,frames=[],backtrace="", hrdprefix="sentry"):
        """
        @param level
            fatal
            error
            warning
            info
            debug

        """

        if j.application.config.exists("%s.server" % hrdprefix):
            import requests
            try:
                import ujson as json
            except:
                import json
            import uuid
            import datetime
            server=j.application.config.get("%s.server" %hrdprefix)
            pub=j.application.config.get("%s.public.key" % hrdprefix)
            secret=j.application.config.get("%s.secret.key" % hrdprefix)
            port=j.application.config.getInt("%s.port" % hrdprefix)
            default=j.application.config.get("%s.project" % hrdprefix)
            url='http://%s:%s/'%(server,port)
            exc={}
            exc["type"]=ttype
            exc["value"]=message

            def ignore(modulename):
                if modulename.strip()=="":
                    return True
                toignore=["errorhandling"]
                for check in toignore:
                    if modulename.find(check)<>-1:
                        return True
                return False
                

            if modulename==None:
                modulename="appname:%s"%(j.application.appname)
                try:
                    if frames==[]:
                        frames=self.getFrames(tb)
                    frame=frames.pop()[0]
                    modulename=""
                    while ignore(modulename):                    
                        modulename=inspect.getmodule(frame)
                        if modulename==None or str(modulename).strip()=="":
                            modulename=inspect.getmodulename(frame.f_code.co_filename)
                        modulename=str(modulename)
                        modulename=modulename.replace("<module ","").replace("'","").replace(".pyc","").replace(">","")
                        try:
                            modulename=modulename.split("from")[0].strip()
                        except:
                            pass
                        if len(frames)>0:
                            frame=frames.pop()[0]
                        else:
                            modulename="appname:%s"%(j.application.appname)
                    if modulename.find("appname")==-1:
                        modulename="appname:%s / %s"%(j.application.appname,modulename)
                except Exception,e:
                    modulename="appname:%s"%(j.application.appname)  

                
            exc["module"]=modulename
            exc=[exc]
            if tags==None:
                tags={}
            else:
                tags=j.core.tags.getObject(tags)
                tags=tags.getDict()
            tags['type'] = ttype

            data={}
            data["event_id"]=uuid.uuid4().hex
            data["culprit"]=modulename
            data["timestamp"]=str(datetime.datetime.utcnow())
            data["message"]="%s" %(message)
            data["tags"]=tags
            data["exception"]=exc
            data["level"]=level
            data["logger"]=j.application.appname
            data["platform"]="python"
            data["server_name"]="g%s.n%s"%(j.application.whoAmI.gid,j.application.whoAmI.nid)  
            data["extra"]=extra

            if tb<>None:
                from stacks import iter_traceback_frames,get_stack_info
                frames=iter_traceback_frames(tb)
                data.update({
                    'sentry.interfaces.Stacktrace': {
                        'frames': get_stack_info(frames)
                    },
                })
            else:
                data.update({
                    'sentry.interfaces.Stacktrace': {
                        'frames': backtrace
                    },
                })


            url2="%s/api/%s/store/"%(url,default)

            auth="Sentry sentry_version=5, sentry_timestamp=%s,"%j.base.time.getTimeEpoch()
            auth+="sentry_key=%s, sentry_client=raven-python/1.0,"%pub
            auth+="sentry_secret=%s"%secret

            headers = {'X-Sentry-Auth': auth}

            try:
                r = requests.post(url2,data=json.dumps(data), headers=headers, timeout=1)
            except Exception,e:  
                pass              
                # print "COULD NOT SEND \n%s \nTO SENTRY.\nReason:%s"%(data,e)