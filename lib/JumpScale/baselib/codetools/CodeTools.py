
from JumpScale.baselib.regextools.RegexTools import RegexTools
from .TemplateEngineWrapper import TemplateEngineWrapper
from .WordReplacer import WordReplacer
from .TextFileEditor import TextFileEditor

class CodeTools:
    def __init__(self):
        self.regex=RegexTools()
        self.templateengine=TemplateEngineWrapper()
        
        #self.wordreplacer=WordReplacer()
    
    def getWordReplacerTool(self):
        return WordReplacer()
    
    def getTextFileEditor(self,filepath):
        """
        returns a class which helps you to edit a text file
        e.g. find blocks, replace lines, ...
        """
        return TextFileEditor(filepath)
    
    def textToTitle(self,text,maxnrchars=60):
        """
        try to create a title out of text, ignoring irrelevant words and making lower case and removing 
        not needed chars
        """
        ignore="for in yes no after up down the"
        ignoreitems=ignore.split(" ")
        keepchars="abcdefghijklmnopqrstuvwxyz1234567890 "
        out=""
        text=text.lower().strip()
        for char in text:
            if char in keepchars:
                out+=char
        text=out
        text=text.replace("  ","")
        text=text.replace("  ","")
        out=""
        nr=0
        for item in text.split(" "):
            if item not in ignoreitems:
                nr+=len(item)
                if nr<maxnrchars:		    
                    out+=item+" "
        if len(text.split(" "))>0:
            text=out.strip()	
        if len(text)>maxnrchars:
            text=text[:maxnrchars]
        return text