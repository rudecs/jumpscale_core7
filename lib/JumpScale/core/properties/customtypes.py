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

'''Descriptors for jumpscale custom types

See the documentation of jumpscale.properties.common for more info.
'''

from JumpScale.core.properties import BaseDescriptor

from JumpScale.core.pmtypes.CustomTypes import Guid
from JumpScale.core.pmtypes.CustomTypes import Path, DirPath, FilePath
from JumpScale.core.pmtypes.CustomTypes import UnixDirPath, UnixFilePath
from JumpScale.core.pmtypes.CustomTypes import WindowsDirPath, WindowsFilePath
from JumpScale.core.pmtypes.CustomTypes import IPv4Address

class Guid(BaseDescriptor):
    '''Descriptor for L{jumpscale.pmtypes.CustomTypes.Guid}'''
    PMTYPE = Guid


class Path(BaseDescriptor):
    '''Descriptor for L{jumpscale.pmtypes.CustomTypes.Path}'''
    PMTYPE = Path


class DirPath(BaseDescriptor):
    '''Descriptor for L{jumpscale.pmtypes.CustomTypes.DirPath}'''
    PMTYPE = DirPath


class FilePath(BaseDescriptor):
    '''Descriptor for L{jumpscale.pmtypes.CustomTypes.FilePath}'''
    PMTYPE = FilePath


class UnixDirPath(BaseDescriptor):
    '''Descriptor for L{jumpscale.pmtypes.CustomTypes.UnixDirPath}'''
    PMTYPE = UnixDirPath


class UnixFilePath(BaseDescriptor):
    '''Descriptor for L{jumpscale.pmtypes.CustomTypes.UnixFilePath}'''
    PMTYPE = UnixFilePath


class WindowsDirPath(BaseDescriptor):
    '''Descriptor for L{jumpscale.pmtypes.CustomTypes.WindowsDirPath}'''
    PMTYPE = WindowsDirPath


class WindowsFilePath(BaseDescriptor):
    '''Descriptor for L{jumpscale.pmtypes.CustomTypes.WindowsFilePath}'''
    PMTYPE = WindowsFilePath


class IPv4Address(BaseDescriptor):
    '''Descriptor for L{jumpscale.pmtypes.CustomTypes.IPv4Address}'''
    PMTYPE = IPv4Address