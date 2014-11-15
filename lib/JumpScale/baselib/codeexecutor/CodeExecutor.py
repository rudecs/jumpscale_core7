from JumpScale import j

class CodeExecutor:
    def __init__(self):
       pass

    def evalFile(self,path):
        content=j.system.fs.fileGetContents(path)
        content=self.eval(content)
        j.system.fs.writeFile(path,content)

    def eval(self,code):
        return j.tools.text.eval(code)

    def _tostr(self,result):
        return j.tools.text.tostr(result)

