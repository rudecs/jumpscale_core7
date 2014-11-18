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

from heapq import heapify, heappop, heappush
from itertools import islice, cycle
from tempfile import gettempdir
import os
from JumpScale import j


class Sort(object):
    def merge(self,chunks,key=None):
	"""
	@todo p3 document  (id:22)
	"""
	if key is None:
	    key = lambda x : x

	values = []

	for index, chunk in enumerate(chunks):
	    try:
		iterator = iter(chunk)
		value = next(iterator)

	    except StopIteration:
		try:
		    chunk.close()
		    os.remove(chunk.name)
		    chunks.remove(chunk)
		except:
		    j.logger.log("StopIterationException", 5)
	    else:
		heappush(values,((key(value),index,value,iterator,chunk)))

	while values:
	    k, index, value, iterator, chunk = heappop(values)
	    yield value
	    try:
		value = next(iterator)

	    except StopIteration:
		try:
		    chunk.close()
		    os.remove(chunk.name)
		    chunks.remove(chunk)
		except:
		    j.logger.log("StopIterationException", 5)
	    else:
		heappush(values,(key(value),index,value,iterator,chunk))

    def batch_sort(self,input, output, header, key=None,buffer_size=32000,tempdirs=[]):
	"""
	@todo p3 document  (id:23)
	"""
	
	if not tempdirs:
	    tempdirs.append(gettempdir())

	input_file = file(input,'rb',64*1024)

	try:
	    input_iterator = iter(input_file)

	    chunks = []
	    try:
		for tempdir in cycle(tempdirs):
		    current_chunk = list(islice(input_iterator,buffer_size))
		    if current_chunk:
			current_chunk.sort(key=key)
			output_chunk = file(os.path.join(tempdir,'%06i'%len(chunks)),'w+b',64*1024)
			output_chunk.writelines(current_chunk)
			output_chunk.flush()
			output_chunk.seek(0)
			chunks.append(output_chunk)
		    else:
			break
	    except:
		for chunk in chunks:
		    try:
			chunk.close()
			os.remove(chunk.name)
		    except:
			j.logger.log("StopIterationException", 5)
		if output_chunk not in chunks:
		    try:
			output_chunk.close()
			os.remove(output_chunk.name)
		    except:
			j.logger.log("StopIterationException", 5)
		return
	finally:
	    input_file.close()

	output_file = file(output,'wb',64*1024)
	try:
	    output_file.write(header[0])
	    output_file.write(header[1])
	    output_file.write(header[2])
	    output_file.write(header[3])
	    output_file.write(header[4])

	    output_file.writelines(merge(chunks,key))

	finally:
	    for chunk in chunks:
		try:
		    chunk.close()
		    os.remove(chunk.name)
		except:
		    j.logger.log("StopIterationException", 5)
	    output_file.close()
	    



