# <License type="Sun Cloud BSD" version="2.2">
#
# Copyright (c) 2005-2009, Sun Microsystems, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# 3. Neither the name Sun Microsystems, Inc. nor the names of other
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY SUN MICROSYSTEMS, INC. "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL SUN MICROSYSTEMS, INC. OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# </License>

'''The jumpscale symbolic debugger subsystem'''

import sys

from JumpScale import j

# Dictionary containing all known debuggers
# Key is name (string), value is a tuple of 2 callables: one to start the actual
# debugger (set a breakpoint), one to perform extra configuration work
DEBUGGERS = dict()


# 'disabled' debugger
def disabled_break(frame, depth): #pylint: disable-msg=W0613
    '''Callback for systems where debugging is disabled'''
    j.logger.log('Debugging disabled on this system', 5)

DEBUGGERS['disabled'] = disabled_break, lambda s: None


# 'pdb' debugger
try:
    import pdb
except ImportError:
    pass
else:
    def pdb_break(frame, depth): #pylint: disable-msg=W0613
        '''Start an interactive debugger session based on PDB'''
        pdb.Pdb().set_trace(frame)

    DEBUGGERS['pdb'] = pdb_break, lambda s: None

# 'ipython' debugger
try:
    from IPython.Debugger import Tracer
    from IPython.excolors import ExceptionColors
except ImportError:
    pass
else:
    IPYTHON_TRACER = None
    def ipython_break(frame, depth, #pylint: disable-msg=W0613
                      color_scheme='Linux'):
        '''Start an interactive debugger session based on the IPython
        debugger'''
        #This code is a pretty dirty hack to get around some obscure
        #IPython issue
        global IPYTHON_TRACER

        if not IPYTHON_TRACER:
            # This is the first time this procedure is called
            # Due to some funky IPython 0.10 internals, we need the following:
            import IPython

            if map(int, IPython.__version__.split('.'))[:2] == [0, 10]:
                from IPython.Shell import IPShellEmbed
                IPShellEmbed(argv=[])

        old_colors = ExceptionColors.active_scheme_name
        ExceptionColors.active_scheme_name = color_scheme

        if not IPYTHON_TRACER:
            IPYTHON_TRACER = Tracer(color_scheme)

        IPYTHON_TRACER.debugger.set_trace(frame)
        ExceptionColors.active_scheme_name = old_colors

    DEBUGGERS['ipython'] = ipython_break, lambda item: None


# 'winpdb' debugger
try:
    import rpdb2
except ImportError:
    pass
else:
    def rpdb2_break(frame, depth): #pylint: disable-msg=W0613
        '''Start an embedded debugger session based on WinPDB/RPDB2'''
        j.logger.log('Starting embedded WinPDB debugger, '
                              'this will sleep until you attach your debug '
                              'client, or the default timeout (300 seconds) '
                              'is reached', 5)
        # Retrieve configuration
        config = j.config.getConfig('jumpscale_debugger')['main']
        password = config['rpdb2_password']
        remote = config['rpdb2_allow_remote']
        remote = remote.lower() not in ('0', 'no', 'false', )

        kwargs = {
            'fAllowRemote': remote,
        }

        import inspect
        # Test whether the installed rpdb2 has 'depth' support, use it if
        # available.
        # See http://groups.google.com/group/winpdb/browse_thread/thread/ \
        #            7114edb52bbd5be0#
        if 'depth' in inspect.getargspec(rpdb2.start_embedded_debugger)[0]:
            kwargs['depth'] = depth + 1
        else:
            j.logger.log('Warning: the debugger will start 2 frames '
                                  'under the calling frame, you\'ll need to '
                                  'jump 2 frames up to debug your own code. '
                                  'A newer version of WinPDB might fix this.',
                                  5)

        #pylint: disable-msg=W0142
        rpdb2.start_embedded_debugger(password, **kwargs)
        #pylint: enable-msg=W0142

    def rpdb2_config_handler(item):
        '''Extra configuration labour for the RPDB2 debugger'''
        item.dialogAskString('rpdb2_password', 'Client password')
        item.dialogAskYesNo('rpdb2_allow_remote', 'Allow remote connections')

    DEBUGGERS['winpdb'] = rpdb2_break, rpdb2_config_handler


def set_trace(frame=None, frame_idx=0):
    '''Start a debugging session using the debugger configured on the
    current system

    @param frame: Start frame to debug (top of stack)
    @type frame: frame
    @param frame_idx: Start frame index (if frame is not given)
    @type frame_idx: number
    '''
    try:
        config = j.config.getConfig('jumpscale_debugger')['main']
        if not config:
            raise RuntimeError('No configuration found')
        debugger = config['type']
    except (KeyError, RuntimeError):
        j.logger.log('No debugger configuration found, debugging '
                              'disabled', 4)
        debugger = 'disabled'

    j.logger.log('Breakpoint, using debugger \'%s\'' % debugger, 4)

    if debugger not in DEBUGGERS:
        raise RuntimeError('Configured debugger %s not supported '
                           'on this system' % debugger)

    # We need to go up one more frame if idx is given
    # since the index is based on our caller
    frame = frame or sys._getframe(frame_idx + 1) #pylint: disable-msg=W0212

    try:
        import traceback
        # traceback.format_stack returns a list of strings like
        # '  File "/foo/bar.py", line 27, in <module>\n    bleh()\n'
        # We want to log where the set_trace call was done, so we need the first
        # item of this list (it's from TopOfStack downwards), and clean up the
        # string we find (remove superfluous spaces, newlines,...) and add some
        # ':'s
        # End result:
        # 'File "/foo/bar.py", line 27, in <module>: bleh()'
        call = ': '.join(s.strip() for s in
                         traceback.format_stack()[0].splitlines())
        j.logger.log('Breakpoint call at %s' % call, 5)
    except Exception: #pylint: disable-msg=W0703, W0704
        # We don't really care if the previous line go wrong somewhere, the log
        # message won't be there but that's not critical at all
        pass

    DEBUGGERS[debugger][0](frame, frame_idx + 1)


from JumpScale.core.config import ConfigManagementItem, ItemSingleClass

class jumpscaleDebuggerConfigurationItem(ConfigManagementItem):
    '''JConfig item class for the configuration of the debugger subsystem'''
    CONFIGTYPE = 'jumpscale_debugger'
    DESCRIPTION = 'jumpscale Debugger'
    KEYS={"type":"Debugger type"}
    def ask(self):
        '''Retrieve all required information to configure the debugger
        subsystem'''
        self.dialogAskChoice('type', 'Debugger type',
                           sorted(DEBUGGERS.keys()))
        type_ = self.params['type']
        handler = DEBUGGERS[type_][1]
        handler(self)

#pylint: disable-msg=C0103
jumpscaleDebuggerConfiguration = ItemSingleClass( \
                                            jumpscaleDebuggerConfigurationItem)
#pylint: enable-msg=C0103

class Debugger:
    '''Hook debugging support on the jumpscale class'''
    def __init__(self):
        self._config = jumpscaleDebuggerConfiguration()

    def configure(self, debugger=None):
        '''Configure the debugger subsystem'''
        if debugger is None:
            return self._config.review() #pylint: disable-msg=E1101

        if debugger == 'winpdb':
            # WinPDB needs interactive input
            return self._config.review()

        return self._config.configure({
            'type': debugger,
        })

    def setbreakpoint(self): #pylint: disable-msg=R0201
        '''Set a breakpoint or launch the configured debugger'''
        set_trace(frame_idx=1)

    def __getattr__(self, name):
        # Backward compatibility (and people used to the PDB interface)
        if name == 'set_trace':
            return self.setbreakpoint

        raise AttributeError(name)

    def shell(self):
        '''Launch an IPython interactive shell in the current namespace'''

        from IPython import embed
        return embed()
