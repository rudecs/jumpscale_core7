
# import sys
# import inspect
# import textwrap
# import operator

from JumpScale import j
from Action import *

import ujson as json


class ActionController(object):
    '''Manager controlling actions'''
    def __init__(self, _output=None, _width=70):
        pass
        # self._actions = list()
        # self._width = _width

    def reset(self,category=None):
        from IPython import embed
        print "DEBUG NOW reset ActionController"
        embed()
        
    def _getPathMD(self,category):
        return "%s/%s.json"%(j.dirs.getStatePath(),category)

    def getActionNamesDone(self,category):
        path=self._getPathMD(category)
        if j.system.fs.exists(path):
            return json.loads(j.do.readFile(path))
        else:
            return []

    def setActionNamesDone(self,action):
        md=self.getActionNamesDone(action.category)        
        if action.name not in md:
            md.append(action.name)
            path=self._getPathMD(action.category)
            j.system.fs.createDir(j.system.fs.getDirName(path))
            j.do.writeFile(path,json.dumps(md))

    def start(self, description="", cmds="",action=None,actionRecover=None,actionArgs={},category="unknown",name="unknown",\
            errorMessage="", resolutionMessage="", loglevel=1,die=True,stdOutput=True,errorOutput=True,retry=1,jp=None):
        '''
        @param id is unique id which allows finding back of action
        @param description: Action description (what are we doing)
        @param errorMessage: message to give when error
        @param resolutionMessage: Action resolution message (how to resolve the action when error)
        @param loglevel: Message level
        @param action: python function to execute
        @param actionRecover: python function to execute when error
        @param actionArgs is dict with arguments
        @param cmds is list of commands to execute on os
        @param state : INIT,RUNNING,OK,ERROR
        '''
        action=Action(description, cmds,action,actionRecover,actionArgs,category,name,errorMessage, resolutionMessage,  loglevel,die,stdOutput,errorOutput,retry,jp=jp)
        
        md=self.getActionNamesDone(action.category)
        if action.name in md:
            print "* %-20s: %-40s %-40s ALREADY DONE"%(action.category,action.name,action.description)
            return

        action.execute()
        if action.state=="OK":
            self.setActionNamesDone(action)


    def clean(self):
        '''Clean the list of running actions'''
        j.logger.log('[ACTIONS] Clearing all actions', 5)
        self._actions = list()
        #TODO Get rid of this when reworking console handling properly
        j.console.showOutput()

    def hasRunningActions(self):
        '''Check whether actions are currently running

        @returns: Whether actions are runnin
        @rtype: bool
        '''
        return bool(self._actions)