import ast
import os
from pprint import pprint


class JumpscriptsDocumentGenerator(object):
    def get_jumpscript_info(self, jumpscript, filename):
        """
        Extracts headers info from a jumpscript source code
        @param jumpscript: jumpscript source code.
        @param filename:   the filename to be printed in the generated documentation

        """
        info = {}
        info['scriptname'] = filename
        parsed = ast.parse(jumpscript)
        for node in ast.walk(parsed):
            if type(node) == ast.FunctionDef:
                if node.name == 'action':
                    info['action_docstring'] = ast.get_docstring(node)
                    break
            elif type(node) == ast.Assign:
                if len(node.targets) == 1:
                    try:
                        id_ = node.targets[0].id
                        value = node.value
                        if type(value) == ast.Str:
                            info[id_] = value.s
                        elif type(value) == ast.Num:
                            info[id_] = value.n
                        elif type(value) == ast.Name:  # boolean maybe?
                            if node.value.id in ['True', 'False']:
                                info[id_] = value.id
                        elif type(value) == ast.List:
                            els = []
                            for x in value.elts:
                                if "s" in dir(x):
                                    els.append(x.s)
                                elif "n" in dir(x):
                                    els.append(x.n)
                                elif "id" in dir(x):
                                    els.append(x.id)
                            info[id_] = str(els)
                    except:
                        pass
        return info

    def as_markdown(self, jsdictinfo):
        """
        Compiles the info obtained by get_jumpscript_info function into a markdown file.
        @param jsdictinfo: jumpscript info dict object.

        """
        descr = jsdictinfo.get('descr', 'No description')
        jsdictinfo['descr'] = """\n```{descr}\n```""".format(descr=descr)
        template = """
# JumpScript: {scriptname}
        """.format(scriptname=os.path.basename(jsdictinfo['scriptname']))
        for k, v in jsdictinfo.items():
            template += "\n#### {k}: {v}".format(k=k, v=v)
        return template

    def generate_jumpscripts_docs(self, src, dest):
        """
        Generates markdown documentation from source to destination directories.
        @param src: source directory of jumpscripts.
        @param dest: destination directory of generated documentation.
        """

        for dirname, subdirs, files in os.walk(src):
            for f in files:
                fullsrcpath = os.path.join(src, dirname, f)
                dirname = os.path.basename(dirname)
                docsdest = os.path.join(dest, dirname)
                fbasename = os.path.basename(fullsrcpath)
                fbasename, ext = os.path.splitext(fbasename)
                fulldestpath = os.path.join(docsdest, fbasename+".md")
                if not os.path.exists(docsdest):
                    os.makedirs(docsdest)
                with open(fullsrcpath) as f:
                    jmpinfo = self.get_jumpscript_info(f.read(), fullsrcpath)
                    md = self.as_markdown(jmpinfo)
                    with open(fulldestpath, "w") as docfile:
                        docfile.write(md)
