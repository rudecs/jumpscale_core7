
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
        print "DEBUG NOW ooo"
        embed()
        
    def _getPathMD(self,category):
        return "%s/actions/%s.json"%(j.dirs.cfgDir,category)

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

        # j.console.hideOutput()

    # def stop(self, failed=False):
    #     '''Stop the currently running action

    #     This will get the latest started action from the action stack and
    #     display a result message.

    #     @param failed: Whether the action failed
    #     @type failed: bool
    #     '''
    #     if not self._actions:
    #         #TODO Raise some exception?
    #         j.logger.log('[ACTIONS] Stop called while no actions are '
    #                               'running at all', 3)
    #         return

    #     action = self._actions.pop()

    #     # If this is the last action, _output_start_count should be 0
    #     if not self._actions:
    #         if not self._output_start_count == 0:
    #             self._output_start_count = 0
    #             #raise StartStopOutputCountException
    #             self._handleStartStopOutputCountMismatch()

    #     try:
    #         action.checkOutputCountIsZero()
    #     except StartStopOutputCountException:
    #         self._handleStartStopOutputCountMismatch()

    #     status = _ActionStatus.DONE if not failed else _ActionStatus.FAILED
    #     if not failed and not self._actions and action.interrupted:
    #         status = _ActionStatus.FINISHED
    #     j.logger.log('[ACTIONS] Stopping action \'%s\', result '
    #                           'is %s' % (action.description, status), 5)
    #     action.writeResult(self._output, status, self._width)

    #     if not self._actions:
    #         #TODO Get rid of this when reworking console handling properly
    #         j.console.showOutput()

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

    # def printOutput(self):
    #     for qa in self._runningActions:
    #         self._output.write('%s\n' % qa.output)

    # def _setActions(self, value):
    #     self._actions = value

    # def startOutput(self):
    #     """
    #     Enable j.console output. Format such that it is nicely shown between action start/stop.
    #     """
    #     j.console.showOutput()

    #     self._output_start_count += 1
    #     if self.hasRunningActions():
    #         self._actions[-1].increaseOutputCount()

    #     if self.hasRunningActions() and not self._actions[-1].interrupted:
    #         # After a START, must make sure to put the last action on "RUNNING"
    #         self._actions[-1].writeResult(self._output, _ActionStatus.RUNNING,
    #                                        self._width)
    #         self._actions[-1].interrupted = True

    # def stopOutput(self):
    #     """
    #     Disable j.console output. Format such that it is nicely shown between action start/stop.
    #     """
    #     if self.hasRunningActions():
    #         try:
    #             self._actions[-1].decreaseOutputCount()
    #         except StartStopOutputCountException:
    #             self._handleStartStopOutputCountMismatch()
    #             return

    #     self._output_start_count -= 1
    #     if self._output_start_count < 0:
    #         self._output_start_count = 0
    #         #raise StartStopOutputCountException
    #         self._handleStartStopOutputCountMismatch()

    #     if self.hasRunningActions() and (self._output_start_count == 0):
    #         j.console.hideOutput()


    # def _handleStartStopOutputCountMismatch(self):
    #     '''Handle a start/stop output count mismatch exception

    #     Reset running action list and output start count.

    #     This will break running actions or might break future actions.
    #     '''
    #     j.logger.log(
    #         '[ACTIONS] Warning: start/stop output count mismatch', 4)
    #     self._actions = list()
    #     self._output_start_count = 0