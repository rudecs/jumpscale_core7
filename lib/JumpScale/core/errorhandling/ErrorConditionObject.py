from JumpScale import j
import copy
import unicodedata
import uuid

try:
    import ujson as json
except ImportError:
    import json


LEVELMAP = {1: 'CRITICAL', 2: 'WARNING', 3: 'INFO', 4: 'DEBUG'}
REVERSEMAP = {v: k for k, v in LEVELMAP.items()}
REVERSEMAP['ERROR'] = 1


class ErrorConditionObject():
    """
    @param type #BUG,INPUT,MONITORING,OPERATIONS,PERFORMANCE,UNKNOWN
    @param level #1:critical, 2:warning, 3:info see j.enumerators.ErrorConditionLevel
    """

    def __init__(self, ddict={}, msg="", msgpub="", category="", level=1, type="UNKNOWN", tb=None, data=None):
        if isinstance(ddict, dict) and ddict != {}:
            self.__dict__ = ddict
        else:

            self.backtrace = ""
            self.backtraceDetailed = ""
            btkis, filename0, linenr0, func0 = j.errorconditionhandler.getErrorTraceKIS(tb=tb)

            if len(btkis) > 1:
                self.backtrace = self.getBacktraceDetailed(tb)
                self.backtraceDetailed = self.backtrace

            self.category = category  # is category in dot notation
            self.errormessage = msg
            self.errormessagePub = msgpub
            self.level = int(level)  # 1:critical, 2:warning, 3:info see j.enumerators.ErrorConditionLevel.
            self.data = data

            if len(btkis) > 1:
                self.code = btkis[-1][0]
                self.funcname = func0
                self.funcfilename = filename0
                self.funclinenr = linenr0
            else:
                self.code = ""
                self.funcname = ""
                self.funcfilename = ""
                self.funclinenr = ""

            self.appname = j.application.appname  # name as used by application
            self.gid = j.application.whoAmI.gid
            self.nid = j.application.whoAmI.nid
            if hasattr(j, 'core') and hasattr(j.core, 'grid') and hasattr(j.core.grid, 'aid'):
                self.aid = j.core.grid.aid
            self.pid = j.application.whoAmI.pid
            self.jid = 0
            self.masterjid = 0

            self.epoch = j.base.time.getTimeEpoch()
            self.type = str(type)  # BUG,INPUT,MONITORING,OPERATIONS,PERFORMANCE,UNKNOWN
            self.tb = tb

            self.tags = ""  # e.g. machine:2323
            self.state = "NEW"  # ["NEW","ALERT","CLOSED"]

            self.lasttime = 0  # last time there was an error condition linked to this alert
            self.closetime = 0  # alert is closed, no longer active

            self.occurrences = 1  # nr of times this error condition happened
            self.noreraise = False
            self.exceptionclassname = None

            self.getUniqueKey()
            self.guid = str(uuid.UUID(self.uniquekey))

    def getUniqueKey(self):
        """
        return unique key for object, is used to define unique id
        """
        if self.category != "":
            C = "%s_%s_%s_%s_%s_%s_%s_%s" % (self.gid, self.nid, self.category, self.level,
                                             self.funcname, self.funcfilename, self.appname, self.type)
        else:
            C = "%s_%s_%s_%s_%s_%s_%s_%s" % (self.gid, self.nid, self.errormessage, self.level,
                                             self.funcname, self.funcfilename, self.appname, self.type)
        self.uniquekey = j.tools.hash.md5_string(C)
        return self.uniquekey

    def toAscii(self):
        def _toAscii(s):
            doagain = False
            try:
                if isinstance(s, unicode):
                    s = unicodedata.normalize('NFKD', s)
                return s.encode('utf-8', 'ignore')
            except Exception:
                # try default
                doagain = True
            if doagain:
                try:
                    s = str(s)
                except Exception:
                    print("BUG in toascii in ErrorConditionObject")
                    import ipdb
                    ipdb.set_trace()

        self.errormessage = _toAscii(self.errormessage)
        self.errormessagePub = _toAscii(self.errormessagePub)
        self.errormessagePub = _toAscii(self.errormessagePub)
        self.backtraceDetailed = _toAscii(self.backtraceDetailed)

    def process(self):
        self.toAscii()

        if not j.basetype.integer.check(self.level):
            try:
                self.level = int(self.level)
            except:
                pass
            if not j.basetype.integer.check(self.level):
                self.level = 1
                j.events.inputerror_warning(
                    "Errorcondition was thrown with wrong level, needs to be int.\n%s" % str(self), "eco.check.level")

        if self.level > 4:
            j.events.inputerror_warning(
                "Errorcondition was thrown with wrong level, needs to be max 4.\n%s" % str(self), "eco.check.level")
            self.level = 4

        res = j.errorconditionhandler._send2Redis(self)
        if res is not None:
            self.__dict__ = res

    def dump(self):
        data = self.__dict__.copy()
        data.pop('tb', None)
        return data

    def toJson(self):
        return json.dumps(self.dump())

    def __str__(self):
        content = "\n\n***ERROR***\n"
        if self.backtrace != "":
            content = "%s\n" % self.backtrace
        content += "type/level: %s/%s\n" % (self.type, self.level)
        content += "%s\n" % self.errormessage
        if self.errormessagePub != "":
            content += "errorpub: %s\n" % self.errormessagePub

        return content

    __repr__ = __str__

    def log2filesystem(self):
        """
        write errorcondition to filesystem
        """
        j.system.fs.createDir(j.system.fs.joinPaths(j.dirs.logDir, "errors", j.application.appname))
        path = j.system.fs.joinPaths(j.dirs.logDir, "errors", j.application.appname,
                                     "backtrace_%s.log" % (j.base.time.getLocalTimeHRForFilesystem()))
        msg = "***ERROR BACKTRACE***\n"
        msg += "%s\n" % self.backtrace
        msg += "***ERROR MESSAGE***\n"
        msg += "%s\n" % self.errormessage
        if self.errormessagePub != "":
            msg += "%s\n" % self.errormessagePub
        if len(j.logger.logs) > 0:
            msg += "\n***LOG MESSAGES***\n"
            for log in j.logger.logs:
                msg += "%s\n" % log

        msg += "***END***\n"

        j.system.fs.writeFile(path, msg)
        return path

    def getBacktrace(self, btkis=None, filename0=None, linenr0=None, func0=None):
        if btkis is None:
            btkis, filename0, linenr0, func0 = j.errorconditionhandler.getErrorTraceKIS()
        out = ""
        # out="File:'%s'\nFunction:'%s'\n"%(filename0,func0)
        # out+="Linenr:%s\n*************************************************************\n\n"%linenr0
        # btkis.reverse()
        for filename, func, linenr, code, linenrOverall in btkis:
            # print "AAAAAA:%s %s"%(func,filename)
            # print "BBBBBB:%s"%linenr
            # out+="%-15s : %s\n"%(func,filename)
            out += "  File \"%s\" Line %s, in %s\n" % (filename, linenrOverall, func)
            c = 0
            for line in code.split("\n"):
                if c == linenr:
                    if len(line) > 120:
                        line = line[0:120]
                    # out+="  %-13s :     %s\n"%(linenrOverall,line.strip())
                    out += "    %s\n" % line.strip()
                #     pre="  *** "
                # else:
                #     pre="      "
                # code2+="%s%s\n"%(pre,line)
                c += 1

            # for line in code2.split("\n"):
            #     if len(line)>90:
            #         out+="%s\n"%line[0:90]
            #         line=line[90:]
            #         while len(line)>90:
            #             line0=line[0:75]
            #             out+="                 ...%s\n"%line0
            #             line=line[75:]
            #         out+="                 ...%s\n"%line
            #     else:
            #         out+="%s\n"%line

            # out+="-------------------------------------------------------------------\n"
        self.backtraceDetailed = out

        return out

        # stack=""
        # if j.application.skipTraceback:
        #     return stack
        # for x in traceback.format_stack():
        #     ignore=False
        #     if x.find("IPython") != -1 or x.find("MessageHandler") != -1 \
        #       or x.find("EventHandler") != -1 or x.find("ErrorconditionObject") != -1 \
        #       or x.find("traceback.format") != -1 or x.find("ipython console") != -1:
        #        ignore=True
        #     stack = "%s"%(stack+x if not ignore else stack)
        #     if len(stack)>50:
        #         self.backtrace=stack
        #         return
        # self.backtrace=stack

    def _filterLocals(self, k, v):
        try:
            k = "{}".format(k)
            v = "{:r<1024.1024}".format(v)
            if k.lower() in ["re", "q", "jumpscale", "pprint", "qexec", "jshell", "Shell", "__doc__", "__file__", "__name__", "__package__", "i", "main", "page", 'eco', 'errorcondition', 'errorconditionobject']:
                return False
            if v.find("<module") != -1:
                return False
            if v.find("IPython") != -1:
                return False
            if v.find("<built-in function") != -1:
                return False
            if v.find("jumpscale.Shell") != -1:
                return False
            if '==== STACKFRAME =====' in v:
                return False
        except:
            return False

        return True

    def getBacktraceDetailed(self, tracebackObject=None, frame=None, startframe=0, framecount=50):
        """
        Get stackframe log
        is a very detailed log with filepaths, code locations & global vars, this output can become quite big
        """
        import inspect
        if j.application.skipTraceback:
            return ""
        sep = "\n" + "-" * 90 + "\n"
        result = ''
        if tracebackObject is None:
            if frame is None:
                frame = inspect.currentframe()
            frames = inspect.getouterframes(frame, 16)[::-1]
        else:
            frames = inspect.getinnerframes(tracebackObject, 16)
        frames = frames[startframe:]
        for (frame, filename, lineno, fun, context, idx) in frames[-framecount:]:
            location = filename + "(line %d) (function %s)\n" % (lineno, fun)
            if location.find("EventHandler.py") == -1:
                result += "  " + sep
                result += "  " + location
                result += "  " + "========== STACKFRAME==========\n"
                if context:
                    l = 0
                    for line in context:
                        prefix = "    "
                        if l == idx:
                            prefix = "--> "
                        l += 1
                        result += prefix + line
                result += "  " + "============ LOCALS============\n"
                for (k, v) in sorted(frame.f_locals.items()):
                    if self._filterLocals(k, v):
                        try:
                            result += "    %.50s : %.1000s\n" % (str(k), str(v))
                        except:
                            pass

        lines = result.split('\n')[:-1000]
        return '\n'.join(lines)

    def getCategory(self):
        return "eco"

    def getObjectType(self):
        return 3

    def getVersion(self):
        return 1

    def getMessage(self):
        return [3, 1, self.guid, self.__dict__]

    def getContentKey(self):
        """
        return unique key for object, is used to define unique id

        """
        dd = copy.copy(self.__dict__)
        if "_ckey" in dd:
            dd.pop("_ckey")
        if "id" in dd:
            dd.pop("id")
        if "guid" in dd:
            dd.pop("guid")
        if "sguid" in dd:
            dd.pop("sguid")
        return j.tools.hash.md5_string(str(dd))
