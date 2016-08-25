from JumpScale import j
import pickle

class JS8Stub:

    def __init__(self):
        self.__jslocation__ = "j.tools.js8stub"
        self.loaded = None

    def generateStub(self, pickledfile="", dest="/tmp/jscompl.py"):
        with open(pickledfile, "rb") as f:
            self.loaded = pickle.load(f)
        with open(dest, "w") as f:
            tmpl = ""
            i=iter(self.loaded.items())
            c, v = next(i) #first one.
            tmpl += self.generate_class(v, 0)
            tmpl = tmpl.replace("\t", "    ") #replace tabs with spaces
            f.write(tmpl)


    def generate_class(self, info, level): #name, type, doc
        name, t, doc, objpath, filepath, extra = info
        #we got all the subclasses of this one
        #and foreach subclass we generate its template based on indenetation level as well
        generated_fields=self.generate_fields_for(objpath, level+1).rstrip() or "{spaces}\tpass".format(spaces=(level+1) * "    ")
        tmpl=""
        tmpl += """
{spaces}class {name}:
{spaces}\tr'''
{spaces}{doc}
{spaces}\t'''
{generated_fields}
        """.format(spaces=level * "    ", doc=doc, name=name, generated_fields=generated_fields)

        return tmpl

    def generate_fields_for(self, objpath, level=0):
        keys=sorted([k for k in self.loaded.keys() if objpath in k and k.count(".") - objpath.count(".")==1])
        vals = [self.loaded[key] for key in keys]
        ret = ""
        for val in vals:

            if len(val) == 6:
                name, t, doc, objp, filepath, extra = val
                if t in ("const"):
                    ret += self.generate_field(val, level)
                if t in  ("method", "property"):
                    ret += self.generate_method(val, level)
                if t in ('class'):
                    ret += self.generate_innerclass(val, level)
        # import pudb; pu.db
        return ret

    def generate_innerclass(self, info, level):
        name, t, doc, objpath, filepath, extra = info
        generated_fields=self.generate_fields_for(objpath, level+1).rstrip() or (level+1)*"    "+"\tpass"

        tmpl = """
{spaces}class {name}:
{generated_fields}
    """.format(spaces=(level)*"    ", name=name, generated_fields=generated_fields)
        return tmpl

    def generate_field(self, info, level):
        name, t, doc, objpath, filepath, extra = info
        return "{spaces}{name} = None\n".format(spaces="    "*level, name=name)

    def generate_method(self, info, level):
        name, t, doc, objpath, filepath, extra = info
        if doc is not None:
            doc=doc.replace("'", '"')
        return """\n
{spaces}@staticmethod
{spaces}def {methodname}({methodargs}):
{spaces}\tr'''
{spaces}{doc}
{spaces}\t'''
{spaces}\tpass\n""".format(spaces=(level)*"    ", methodname=name, methodargs=extra or '', doc=doc)
