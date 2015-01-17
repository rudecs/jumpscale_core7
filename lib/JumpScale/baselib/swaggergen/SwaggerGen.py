from JumpScale import j
import json as json
import jinja2
import urlparse

class SwaggerGen(object):
    def __init__(self):
        self.jinjaEnv = jinja2.Environment(
            loader=jinja2.FileSystemLoader('templates'),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.spec = None
        self.definitions = {}
        self.baseURL = ""
        self.requires = []
        self.handlers = []
        self.output = ""

    def loadSpec(self, path):
        content = j.system.fs.fileGetContents(path)
        self.spec = json.loads(content)

    def generateServer(self, outputPath):
        self._renderRequire()
        self._renderHandlers()
        self._renderApplication()
        j.system.fs.writeFile(outputPath,self.output.strip())
        j.system.fs.writeFile("handler.json",json.dumps(self.handlers,indent=4))
        # from IPython import embed;embed()

    def generateSporeSpec(self, outputPath):
        pass

    def _generateBaseURL(self):
        url = {}
        if 'host' in self.spec:
            if self.spec['host'].find(':') == -1:
                url['host'] = self.spec['host']+":80"
            else:
                url['host'] = self.spec['host']
        else:
            url['host'] = "0.0.0.0:80"
        url['basePath'] = self.spec['basePath'] if 'basePath' in self.spec else "/"
        url['scheme'] = self.spec['scheme'] if 'scheme' in self.spec else "http"
        self.baseURL = urlparse.urlparse(url['scheme']+"://"+url['host']+url['basePath'])

    def _generateHandlers(self):
        if 'definitions' in self.spec:
            self._generateDefinitions(self.spec['definitions'])
        paths = self._generatePaths(self.spec['paths'])
        self.handlers.extend(paths)

    def _generatePaths(self, specPaths):
        def formatPath(s):
            while True:
                start , end = s.find('{'), s.find('}')
                if start == -1 or end == -1:
                    if 'basePath' in self.spec:
                        return self.spec['basePath']+s
                    else:
                        return s
                else:
                    s = s[:start]+"(.*)"+s[end+1:]

        paths = []
        for path,methods in specPaths.iteritems():
            p = {}
            p['name'] = path.replace('/','').replace('{','').replace("}","")
            p['path'] = formatPath(str(path))
            p['methods'] = self._generateMethods(methods)
            paths.append(p)
        paths = sorted(paths, key=lambda path: path['path'],reverse=True)   # sort by path
        return paths

    def _generateMethods(self, specMethods):
        methods = []
        for name,detail in specMethods.iteritems():
            m = {
                'args':{},
                'responses':[],
                'summary':"",
                'name':name
            }
            if 'parameters' in detail:
                m['args'] = self._generateParams(detail['parameters'])
            if 'responses' in detail:
                m['responses'] = self._generateResponses(detail['responses'])
            if 'summary' in detail:
                m['summary'] = detail['summary']
            methods.append(m)
        return methods

    def _generateParams(self, specParams):
        params = {
            'body':[],
            'query':[],
            'path':[],
            'header':[],
            'formData':[]
        }
        for p in specParams:
            # replace ref with actual definition
            if 'schema' in p and '$ref' in p['schema']:
                ss = p['schema']['$ref'].split('/')
                p['schema'] = self.definitions[ss[2]]
            # TODO ref in array
            # if p['in'] == 'body' and 'type' in p['schema'] and p['schema']['type'] == 'array':
            #     ss = p['schema']['items']['$ref'].split("/")
            #     p['schema']['items'] = self.definitions[ss[2]]

            params[str(p['in'])].append(p)
        return params

    def _generateResponses(self, specReponses):
        responses = []
        # import ipdb; ipdb.set_trace()
        for code, detail in specReponses.iteritems():
            r = {}
            r['code'] = code
            r['description'] = detail['description']
            if 'examples' in detail:
                r['examples'] = detail['examples']
            if 'headers' in detail:
                r['headers'] = detail['headers']
            if 'schema' in detail:
                if '$ref' in detail['schema']:
                    ss = detail['schema']['$ref'].split("/")
                    r['schema'] = self.definitions[ss[2]]
                else:
                    r['schema'] = detail['schema']
            responses.append(r)
        return responses

    def _generateDefinitions(self, specDefinitions):
        refs = [] # keeps the refs that need to be linked when all definitions are loaded
        for name, detail in specDefinitions.iteritems():
            self.definitions[name] = detail
            if 'properties' in detail:
                for propName, propDetail in detail['properties'].iteritems():
                    if '$ref' in propDetail:
                        ss = propDetail['$ref'].split('/')
                        r = {
                            'defName':name,
                            'propName':propName,
                            'ref':ss[2],
                            'isArray': False
                        }
                        refs.append(r)
                    elif 'type' in propDetail and propDetail['type'] == 'array' and '$ref' in propDetail['items']:
                        ss = propDetail['items']['$ref'].split('/')
                        r = {
                            'defName':name,
                            'propName':propName,
                            'ref':ss[2],
                            'isArray': True
                        }
                        refs.append(r)
        for r in refs:
            if r['isArray']:
                self.definitions[r['defName']]['properties'][r['propName']]['items'] = self.definitions[r['ref']]
            else:
                self.definitions[r['defName']]['properties'][r['propName']] = self.definitions[r['ref']]

    def _renderRequire(self):
        self.requires.append('turbo')

        tmpl = self.jinjaEnv.get_template('require.tmpl')
        r = tmpl.render(requires=self.requires)
        self.output += r

    def _renderHandlers(self):
        self._generateHandlers()
        tmpl = self.jinjaEnv.get_template('handler.tmpl')
        for h in self.handlers:
            r = tmpl.render(handler=h)
            self.output += r

    def _renderApplication(self):
        self._generateBaseURL()
        if len(self.handlers) == 0:
            self._generateHandlers()
        tmpl = self.jinjaEnv.get_template('application.tmpl')
        r = tmpl.render(handlers=self.handlers, port=8080,url=self.baseURL.hostname+self.baseURL.path)
        self.output += r

if __name__ == '__main__':
    gen = SwaggerGen()
    gen.loadSpec("tests/spec2.json")
    gen.generate('output.lua')


# spore = {
#     'name':'', #required
#     'authority':'',
#     'base_url':'',
#     'formats':[],
#     'version':'', #required
#     'authentication':True,
#     'methods':{}, #required
#     # methods format
#     {
#         'name' :{
#             'methods': '', #required
#             "description" : "",
#             "documentation" : "",
#             'authentication" : false,
#             'path': '/example/:args', #required
#             "optional_params" : [
#               "param"
#             ],
#             "required" : [ #required
#               "args"
#             ],
#             "expected" : [
#               200,
#               204
#             ],
#              "format" : [
#               "json",
#               "xml"
#             ]
#         }
#     }
# }