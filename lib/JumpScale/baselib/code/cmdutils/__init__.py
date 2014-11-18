from JumpScale import j

import JumpScale.baselib.jpackages #load jpackages

import argparse
import sys

class ArgumentParser(argparse.ArgumentParser):
    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, sys.stderr) 
        if j.application.state == "RUNNING":
            j.application.stop(status)
        else:
            sys.exit(status)


def processLogin(parser):

    parser.add_argument("-l",'--login', help='login for grid, if not specified defaults to root')
    parser.add_argument("-p",'--passwd', help='passwd for grid')
    parser.add_argument("-a",'--addr', help='ip addr of master, if not specified will be the one as specified in local config')

    opts = parser.parse_args()

    if opts.login==None:
        opts.login="root"

    # if opts.passwd==None and opts.login=="root":
    #     if j.application.config.exists("grid.master.superadminpasswd"):
    #         opts.passwd=j.application.config.get("grid.master.superadminpasswd")
    #     else:
    #         opts.passwd=j.console.askString("please provide superadmin passwd for the grid.")

    # if opts.addr==None:    
    #     opts.addr=j.application.config.get("grid.master.ip")

    return opts


def getJPackage(args, installed=None,debug=None,update=False,expandInstances=True):

    packages=[]

    if args.installed==None and installed!=None:
        args.installed=installed

    if args.name==None:
        args.name=""

    if args.name.strip()!="":
        for pname in args.name.split(","):
            if pname.strip()!="":
                packages += j.packages.find(name=pname, domain=args.domain, version=args.version,installed=args.installed,instance=args.instance,expandInstances=expandInstances,interactive=False)
    else:
        packages += j.packages.find(name=None, domain=args.domain, version=args.version,installed=args.installed,instance=args.instance,expandInstances=expandInstances,interactive=True)

    if debug==False:
        debugpackages=j.packages.getDebugPackages()
        packages=[item for item in packages if item not in debugpackages]

    # if update:
    #     # raise RuntimeError("not supported for now, this update feature, need to check what it does (kds)")
    #     # packages=[item for item in packages if item.isNew()]

    #     if not j.application.sandbox:
    #         basepackageTest=[item for item in packages if item.name=="base"]

    #         if len(basepackageTest)>0:
    #             print "update base package first and then restart your update (you can see a segmentation fault when you update base)."
    #             print "IMPORTANT do: 'jpackage install -n base'"
    #             print "do this untill it says that it does need to install anymore (installed)"                
    #             j.application.stop(1)

    # if j.application.sandbox:
    #     packages=[item for item in packages if not item.name=="base"]


    if len(packages) == 0:
        if args.installed==True:
            print("Could not find package with name '%s' in domain '%s' with version '%s' and instance '%s' which is installed." % (args.name, args.domain, args.version,args.instance))
        else:
            print("Could not find package with name '%s' in domain '%s' with version '%s' and instance '%s'" % (args.name, args.domain, args.version,args.instance))
        j.application.stop(1)
    elif len(packages) > 1 and args.name.find("*")!=-1:
        pass #no need to ask interactive
    elif len(packages) > 1:
        if not j.application.interactive:
            print("Found multiple packages %s" % (packages))
            j.application.stop(1)
        else:
            packages = j.console.askChoiceMultiple(packages, "Multiple packages found. Select:")

    if args.deps:
        for p in packages:
            for dep in p.getDependencies():
                if dep not in packages:
                    packages.append(dep)

    return packages

def getProcess(parser=None):
    parser = parser or ArgumentParser()
    parser.add_argument('-d', '--domain', help='Process domain name')
    parser.add_argument('-n', '--name', help='Process name')
    return parser.parse_args()
