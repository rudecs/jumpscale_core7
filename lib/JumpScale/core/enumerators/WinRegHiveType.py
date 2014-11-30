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
    raise "WinRegHiveType enumerator is only supported on Windows operating system"

from JumpScale.core.baseclasses import BaseEnumeration
import _winreg as reg

class WinRegHiveType(BaseEnumeration):
    ''' The windows registry hive, or section '''

    def __init__(self, hive):
        self.hive = hive

    def __repr__(self):
        return str(self)

    
WinRegHiveType.registerItem('hkey_classes_root', reg.HKEY_CLASSES_ROOT)
WinRegHiveType.registerItem('hkey_current_user', reg.HKEY_CURRENT_USER)
WinRegHiveType.registerItem('hkey_local_machine', reg.HKEY_LOCAL_MACHINE)
WinRegHiveType.registerItem('hkey_users', reg.HKEY_USERS)
WinRegHiveType.registerItem('hkey_current_config', reg.HKEY_CURRENT_CONFIG)
WinRegHiveType.finishItemRegistration()
