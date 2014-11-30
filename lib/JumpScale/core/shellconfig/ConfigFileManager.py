
from JumpScale import j
import os
import collections


class ParamDetail:
    def __init__(self,nr,name):
        self.nr=nr
        self.name=name
        self.value=""
        self.modified=False

class ConfigFileManager():


    def __init__(self,configType):
        self._configType=configType
        self._loaded=False
        self.cfg=None

    def _getConfigFile(self):
        if self._loaded==False:
            cfgfile=configsDir+os.sep+"%s.cfg" % self._configType
            
            if j.system.fs.exists(cfgfile):
                self.cfg=j.tools.inifile.open(cfgfile)
            else:
                self.cfg=j.tools.inifile.new(cfgfile)
            self._loaded=True
        return self.cfg

    def validateSectionInteractive(self,section,descr="",confirm=True):
        """
        show all settings from a specific section and ask for confirmation if correct, if not ask to change
        """
        if j.application.shellconfig.interactive==False:
            raise Exception("Running non interactive, script is asking to review a config file, please adjust section %s in configfile cfg/%s.cfg" % (section,self._configType))

        cfg=self._getConfigFile()
        params=cfg.getParams(section)
        j.console.echo("")
        if descr=="" and confirm==False:
            descr="##### %s OF %s #####" % (section,self._configType)
        else:
            descr="##### REVIEW CONFIG SECTION %s OF %s #####" % (section,self._configType)

        j.console.echo(descr)
        nr=0
        params2={}
        for param in params:
            nr=nr+1            
            params2[nr]=ParamDetail(nr,param)
            value=cfg.getValue(section,param)
            params2[nr].value=value
            j.console.echo("    %s : %s = %s " % (nr,param,value))
        j.console.echo("")
        if confirm:
            yesno=j.console.askYesNo("Is this correct?")
            if yesno==False:
                #mistakes in config, ask which line
                nr=j.console.askInteger("Which line is not correct?")
                if nr in params2:
                    parameterName=params2[nr].name
                    newvalue= j.console.askString("Give appropriate new value for parameter %s" % parameterName)
                    cfg.setParam(section,parameterName,newvalue)
                    cfg.write()
                    self.validateSectionInteractive(section)
                else:
                    j.console.echo ("ERROR: please specify appropriate line nr")
                    self.validateSectionInteractive(section)

    def showSection(self,section,descr=""):
        """
        show all settings from a specific section
        """
        return self.validateSectionInteractive(section,descr,confirm=False)

    def _askString(self,description,section):
        if j.application.shellconfig.interactive:
            j.console.askString(description)
        else:
            raise 

    def getSetParam(self,section,paramName,description="",value="",default=""):
        """
        if parameter filled in it will set it, 
        if not filled in 
          it will read it from config file, 
          if "" in configfile it will ask for a value
        if you want none in config file mark *NONE*
        """
        self._getConfigFile()
        #self.cfg.addSection(section)
        #print section+" "+paramName+" "+str(value)
        if value is None:
            value="*NONE*"
        if value:
            self.setParam(section,paramName,value)
            result = value
        else:
            result=self.getParam(section,paramName,description,value,False,False)
            if default and not result:
                self.setParam(section,paramName,default)
                result = default
        return result
        

    def getParamAndFix(self,section,paramname,fixmethod):
        try:
            val=self.cfg.getValue(section,paramname)  
        except:            
            return fixmethod(section,paramname)
        return val

    def getParam(self,section,paramName,description="",defaultValue="",forceDefaultValue=False,forceAsk=False,password=False):
        """
        is default configuration management which is personal per user of jumpscale e.g. personal svn connections
        this method allows you to get a parameter, if not found it will interactive ask for that parameter and store it in the apropriate .cfg file in the jumpscale cfg dir
        """
        self._getConfigFile()
        #if forceDefaultValue:
        #    forceDefaultValueStr="TRUE"
        #else:
        #    forceDefaultValueStr="FALSE"
        configType=self._configType
        if section=="" or configType=="":
            raise Exception("cannot get parameter when section or configType not specified")
        j.logger.log("get param: configtype %s, section %s, param %s, defaulvalue %s, forceDefaultValue %s" % (configType,section,paramName,defaultValue,forceDefaultValue))
        maincfg=self._getConfigFile()
        maincfg.addSection(section)
        if maincfg.checkParam(section,paramName)==False or maincfg.getValue(section,paramName)=="" or forceAsk:
            if defaultValue!="":
                description2= " (default value: %s)" % defaultValue
            else:
                description2=""
            if description=="":
                description="Please provide input for parameter %s in section %s in configuration %s. %s" % (paramName,section,configType, description2)
            else:
                description="%s%s" % (description,description2)
            if forceDefaultValue==True and defaultValue!="":
                value= defaultValue
            if forceDefaultValue==True and defaultValue==None:
                value="*NONE*"
            if forceDefaultValue==False or defaultValue=="":
                if j.application.shellconfig.interactive:
                    if not password:
                        value= j.console.askString(description)
                    else:
                        value= j.console.askPassword(description)
                else: 
                    raise Exception("Parameter not configured yet in config file: %s, section:%s , param:%s. Please fix. \nTIP You can also put jshell in interactive mode (j.application.shellconfig.interactive=True):" %(self._configType,section,paramName))
                if value=="":
                    value=defaultValue
            maincfg.setParam(section,paramName,value)
            maincfg.write()
        else:
            value=maincfg.getValue(section,paramName)
        if value == "notset" or value == "none" or value==None:
            maincfg.setParam(section,paramName,"*NONE*")
            value=None
            maincfg.write()
        if value=="*NONE*":
            value=None
        return value
    
    def getParams(self, section):
        """
        Returns all parameter names in the section.

        @param section: section of which the parameter names should be returned
        @type section: string
        @return: list of string names of parameters
        """
        return self._getConfigFile().getParams(section)

    def checkParam(self,section,paramName):
        self._getConfigFile()
        return self._getConfigFile().checkParam(section,paramName)

    def setParam(self,section,paramName,value):
        self._getConfigFile()
        self.cfg.addSection(section)
        self.cfg.setParam(section,paramName,value)
        self.cfg.write()

    def chooseSectionInteractive(self,sectionDescription="section", sort=False):
        """
        multiple choice of section in configtype
        return name
        """
        self._getConfigFile()
        if j.application.shellconfig.interactive==False:
            raise Exception("Running non interactive, script is asking for interactive input (choice of item), looking for %s in configfile %s" % (sectionDescription,self._configType))
        cfg=self._getConfigFile()
        sections=cfg.getSections()

        if sort:
            if isinstance(sort, collections.Callable):
                #Custom sort method
                sections = sort(sections)
            else:
                #Plain ascii sort
                sections = sorted(sections)

        j.console.echo("\nWhich %s do you want to choose: " % (sectionDescription))
        nr=0
        for section in sections:
            nr=nr+1
            j.console.echo("   %s: %s" % (nr, section))
        j.console.echo("")
        result=j.console.askInteger("   Select Nr")
        if result>0 and result < nr+1:
            return sections[result-1]    
        else:
            raise Exception ("Cannot continue did not make right selection, please try again")

    def getSections(self):
        """
        return array of found sections in config file
        """
        cfg=self._getConfigFile()
        sections=cfg.getSections()       
        return sections

    def removeSection(self,sectionName):        
        cfg=self._getConfigFile()
        cfg.removeSection(sectionName)  
        cfg.write()