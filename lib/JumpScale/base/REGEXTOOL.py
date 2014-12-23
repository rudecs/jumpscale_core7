from JumpScale import j

try:
    import regex
except:    
    pass

class REGEXTOOL():

    @staticmethod       
    def match(pattern,text):
        m = regex.match(pattern,text)
        if m:
            print("%s %s"%(pattern,text))
            return True
        else:
            return False        

    @staticmethod           
    def matchContent(path,contentRegexIncludes=[], contentRegexExcludes=[]):
        content=j.system.fs.fileGetContents(path)
        if REGEXTOOL.matchMultiple(patterns=contentRegexIncludes,text=content) and not REGEXTOOL.matchMultiple(patterns=contentRegexExcludes,text=content):
            return True
        return False

    @staticmethod       
    def matchMultiple(patterns,text):
        """
        see if any patterns matched
        if patterns=[] then will return False
        """
        if type(patterns).__name__!='list' :
            raise RuntimeError("patterns has to be of type list []")
        if patterns==[]:
            return True
        for pattern in patterns:
            pattern=REGEXTOOL._patternFix(pattern)
            if REGEXTOOL.match(pattern,text):
                return True
        return False


    @staticmethod       
    def matchPath(path,regexIncludes=[],regexExcludes=[]):
        if REGEXTOOL.matchMultiple(patterns=regexIncludes,text=path) and not REGEXTOOL.matchMultiple(patterns=regexExcludes,text=path):
            return True
        return False        

    @staticmethod       
    def _patternFix(pattern):
        if pattern.find("(?m)")==-1:
            pattern="%s%s" % ("(?m)",pattern)
        return pattern        


j.base.regex=REGEXTOOL
