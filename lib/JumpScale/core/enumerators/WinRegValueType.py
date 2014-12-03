# Copyright (c) 2008, Q-layer NV
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the jumpscale nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY Q-LAYER ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Q-LAYER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
if not sys.platform.startswith('win'):
    raise "WinRegValueType enumerator is only supported on Windows operating system"

from JumpScale.core.baseclasses import BaseEnumeration
import _winreg as reg

class WinRegValueType(BaseEnumeration):
    ''' The windows registry value type'''

    def __init__(self, type, exportPrefix):
        self.type = type
        self.exportPrefix = exportPrefix

    def __repr__(self):
        return str(self)
    
    def findByIntegerValue(self, integerValue):
        for item in self._pm_enumeration_items:
            vt = WinRegValueType.getByName(item)
            if vt.type == integerValue:
                return vt
        raise KeyError("No WinRegValueType found with integer value '%s'"%integerValue)

    def findByExportPrefix(self, exportPrefix):
        for item in self._pm_enumeration_items:
            vt = WinRegValueType.getByName(item)
            if vt.exportPrefix == exportPrefix:
                return vt
        raise KeyError("No WinRegValueType found with export prefix '%s'"%exportPrefix)
    
    findByIntegerValue = classmethod(findByIntegerValue)
    findByExportPrefix = classmethod(findByExportPrefix)
    
WinRegValueType.registerItem('binary', reg.REG_BINARY, 'hex')
WinRegValueType.registerItem('dword', reg.REG_DWORD, 'dword')
WinRegValueType.registerItem('string', reg.REG_SZ, None)
WinRegValueType.registerItem('multi_string', reg.REG_MULTI_SZ, 'hex(7)')
WinRegValueType.registerItem('expandable_string', reg.REG_EXPAND_SZ, 'hex(2)')
WinRegValueType.finishItemRegistration()
