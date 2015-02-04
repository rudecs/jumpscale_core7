import sys
from JumpScale import j
import imp
import JumpScale.grid.osis
import inspect

class FileLikeStreamObject(object):
    def __init__(self):
        self.out=""

    def write(self, buf,**args):
        for line in buf.rstrip().splitlines():
            #print "###%s"%line
            self.out+="%s\n"%line

 

class Test():
    def __init__(self,db,testclass):
        self.db=db
        self.testclass=None
        self.eco=None

    def execute(self,testrunname,debug=False):

        def testDebug(code):
            return self.db.source[name].find("import ipdb")!=-1 or self.db.source[name].find("import embed")!=-1
        print(("\n##TEST:%s %s"%(self.db.organization,self.db.name)))
        self.testclass.setUp()
        print("setup")
        
        print((self.db.path))
        for test in inspect.getmembers(self.testclass):
            if str(test[0]).find("test_")==0:
                #found test
                name=test[0][5:]
                print(("execute test:%-30s"%name))

                out=FileLikeStreamObject()

                
                if debug==False and testDebug(self.db.source[name])==False:            
                    sys.stdout = out
                    sys.stderr = out
                
                try:
                    self.db.result=test[1]()
                except Exception as e:
                    sys.stdout =j.tools.testengineKds.sysstdout
                    sys.stderr =j.tools.testengineKds.sysstderr  
                    print("ERROR IN TEST:")
                    print((out.out))
                    eco=j.errorconditionhandler.parsePythonErrorObject(e)
                    eco.tags="testrunner testrun:%s org:%s testgroup:%s testname:%s testpath:%s" % (self.db.testrun,\
                            self.db.organization, self.db.name,name,self.db.path)
                    eco.process()                    
                    if debug:
                        sys.exit()
                sys.stdout =j.tools.testengineKds.sysstdout
                sys.stderr =j.tools.testengineKds.sysstderr
                print("ok")
                self.db.output[name]=out.out
        try:
            self.testclass.tearDown()
        except Exception as e:
            pass

    def __str__(self):
        out=""
        for key,val in list(self.db.__dict__.items()):
            if key[0]!="_" and key not in ["source","output"]:
                out+="%-35s :  %s\n"%(key,val)
        items=out.split("\n")
        items.sort()
        return "\n".join(items)

    __repr__ = __str__




class TestEngineKds():
    def __init__(self):
        self.paths=[]
        self.tests=[]
        self.outputpath="%s/apps/gridportal/base/Tests/TestRuns/"%j.dirs.baseDir
        self.sysstdout=sys.stdout
        self.sysstderr=sys.stderr        

    def initTests(self,osisip="127.0.0.1",login="",passwd="",noOsis=False): #@todo implement remote osis
        client = j.clients.osis.get(user="root")
        self.osis=j.clients.osis.getCategory(client, 'system', 'test')
        self.noOsis=noOsis

    def runTests(self,testrunname=None,debug=False):

        if testrunname==None:
            testrunname=j.base.time.getLocalTimeHRForFilesystem()

        for path in self.paths:
            print(("scan dir: %s"%path))
            for item in j.system.fs.listFilesInDir(path,filter="*__test.py",recursive=True):
                testdb=self.osis.new()
                name=j.system.fs.getBaseName(item).replace("__test.py","").lower()
                testmod = imp.load_source(name, item)

                if not testmod.enable:
                    continue

                testclass=testmod.TEST()

                test=Test(testdb,testclass)

                test.db.author=testmod.author
                test.db.descr=testmod.descr.strip()
                test.db.organization=testmod.organization
                test.db.version=testmod.version
                test.db.categories=testmod.category.split(",")
                test.db.enable=testmod.enable
                test.db.license=testmod.license
                test.db.priority=testmod.priority
                test.db.gid=j.application.whoAmI.gid
                test.db.nid=j.application.whoAmI.nid
                test.db.state="INIT"
                test.db.testrun=testrunname
                test.db.name=name
                test.db.path=item
                test.db.priority=testmod.priority
                test.db.id=0
                test.db.send2osis=getattr(testmod,"send2osis",False)

                C=j.system.fs.fileGetContents(item)
                methods=j.codetools.regex.extractBlocks(C,["def test"])
                for method in methods:
                    methodname=method.split("\n")[0][len("    def test_"):].split("(")[0]
                    methodsource="\n".join([item.strip() for item in method.split("\n")[1:] if item.strip()!=""])
                    test.db.source[methodname]=methodsource

                test.testclass=testclass
                self.osis.set(test.db)
                self.tests.append(test)

        print("all tests loaded in osis")

        priority={}
        for test in self.tests:
            if test.db.priority not in priority:
                priority[test.db.priority]=[]    
            priority[test.db.priority].append(test)
        prio=list(priority.keys())
        prio.sort()
        for key in prio:
            for test in priority[key]:
                #now sorted
                # print test
                test.execute(testrunname=testrunname,debug=debug)
                if test.db.send2osis and not(self.noOsis):
                    self.osis.set(test.db)


                
