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

from JumpScale import j
import pg

class DBConnection(object):
    """
    only support postgresql for now
    """

    def __init__(self, ip, dbname, login, passwd=None):
        kwargs = dict()
        if ip:
            kwargs['host'] = ip
        if dbname:
            kwargs['dbname'] = dbname
        if login:
            kwargs['user'] = login
        if passwd:
            kwargs['passwd'] = passwd
        self._connection = pg.connect(**kwargs)
        self.__db = pg.DB(self._connection)
        self.defaultowner="postgres"
        self.metadatapopulated=False

    def sqlexecute(self,sql):
        try:
            return self._connection.query(sql)
        except:
            self._connection.reset()
            raise

    def getDatabaseMetadata(self):
        """
        fetch all relevant metadata about database e.g. tablespaces, tables, columns, ... store in tablespacesReality
        make sure this only happens once per dbconnection
        """
        if self.metadatapopulated==False:
            pass #populate tablespacesReality array in this object

    def existsTable(self,tablename,tablespace=""):
        self.getDatabaseMetadata() #make sure metadata info is populated
        #ttodo

    def existsTableColumn(self,tablename,columnname,tablespace=""):
        self.getDatabaseMetadata() #make sure metadata info is populated
        #ttodo

    def listTables(self,tablespace=""):
        return self.__db.get_tables()

    def listColumns(self,tablename,tablespace=""):
        return self._get_attnames(tablename if not tablespace else "%s.%s"%(tablespace, tablename))

    def _get_attnames(self, cl):
        cl = self.__db._split_schema(cl)
        qcl = pg._join_parts(cl)
        if qcl in self.__db._attnames:
            return self.__db._attnames[qcl]
        if qcl not in self.__db.get_relations('rv'):
            raise pg.ProgrammingError('Class %s does not exist' % qcl)
        t = {}
        for att, typ in self.__db.db.query("SELECT pg_attribute.attname,"
            " pg_type.typname FROM pg_class"
            " JOIN pg_namespace ON pg_class.relnamespace = pg_namespace.oid"
            " JOIN pg_attribute ON pg_attribute.attrelid = pg_class.oid"
            " JOIN pg_type ON pg_type.oid = pg_attribute.atttypid"
            " WHERE pg_namespace.nspname = '%s' AND pg_class.relname = '%s'"
            " AND (pg_attribute.attnum > 0 or pg_attribute.attname = 'oid')"
            " AND pg_attribute.attisdropped = 'f'"
                % cl).getresult():
            if typ.startswith('bool'):
                t[att] = 'bool'
            elif typ.startswith('abstime') or typ.startswith('date') or typ.startswith('interval'):
                t[att] = 'date'
            elif typ.startswith('timestamp'):
                t[att] = 'datetime'
            elif typ.startswith('money'):
                t[att] = 'money'
            elif typ.startswith('numeric'):
                t[att] = 'num'
            elif typ.startswith('float'):
                t[att] = 'float'
            elif typ.startswith('int') or typ.startswith('oid'):
                t[att] = 'int'
            elif typ.startswith('uuid'):
                t[att] = 'uuid'
            else:
                t[att] = 'text'
        self.__db._attnames[qcl] = t # cache it
        return self.__db._attnames[qcl]

    def __del__(self):
        # If something goes wrong during __init__, the _connections attribute
        # might not exist - Trac #157
        connection = getattr(self, '_connection', None)

        if not connection:
            return

        connection.close()
