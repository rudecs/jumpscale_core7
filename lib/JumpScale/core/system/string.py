
import unicodedata

class String:
    #exceptions = Exceptions
    
    def decodeUnicode2Asci(self,text):
        return unicodedata.normalize('NFKD', text.decode("utf-8")).encode('ascii','ignore')
        
    def toolStripNonAsciFromText(self,text):	
        return "".join([char for char in str(text) if ((ord(char)>31 and ord(char)<127) or ord(char)==10)])
    