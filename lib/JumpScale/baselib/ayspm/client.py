import requests
import json
import inspect

class AYSPMClient(object):
    """client for process manager server api"""
    def __init__(self, baseurl=""):
        self.baseurl = baseurl
        self.contentType = 'application/json'
        self.accept = 'application/json'

        self.session = requests.Session()
        self.session.headers.update({
            'Accept' : self.accept,
            'Content-Type' : self.contentType
            })

    def _buildRequest(self, url, type, data=None,headers={}):
        req = requests.Request(type, url, data=data, headers=headers)
        return self.session.prepare_request(req)

    def createProcess(self, function, args, start=True):
        url = "%s/process/" % self.baseurl
        s=""
        if hasattr(function, '__call__'):
            s=inspect.getsource(function)
        elif isinstance(function,basestring):
            s=function
        else:
            raise RuntimeError('function should be a string or a function')
        data = {
            'code':s,
            'args':args
        }
        sData = json.dumps(data)

        req = self._buildRequest(url, 'POST', data=sData)
        resp = self.session.send(req)
        if resp.status_code == requests.codes.ok:
            return resp.json()
        else:
            resp.raise_for_status()

    def killProcess(self, pid):
        url = "%s/process/%s" % (self.baseurl,pid)
        req = self._buildRequest(url, 'DELETE')
        resp = self.session.send(req)

        if resp.status_code == requests.codes.ok:
            return resp.json()
        else:
            resp.raise_for_status()

    def getProcess(self, pid):
        url = "%s/process/%s" % (self.baseurl,pid)
        req = self._buildRequest(url, 'GET')
        resp = self.session.send(req)

        if resp.status_code == requests.codes.ok:
            return resp.json()
        else:
            resp.raise_for_status()

    def listProcesses(self):
        url = "%s/process/" % self.baseurl
        req = self._buildRequest(url, 'GET')
        resp = self.session.send(req)

        if resp.status_code == requests.codes.ok:
            return resp.json()
        else:
            resp.raise_for_status()

class AYSPMClientFactory(object):
    def getClient(self):
        return AYSPMClient()
