from JumpScale import j
import JumpScale.grid.agentcontroller
import JumpScale.grid.osis
import JumpScale.baselib.units
import gevent
import json

class GridHealthChecker(object):

    def __init__(self):
        with j.logger.nostdout():
            self._client = j.clients.agentcontroller.get()
            self._osiscl = j.clients.osis.getByInstance('main')
        self._heartbeatcl = j.clients.osis.getCategory(self._osiscl, 'system', 'heartbeat')
        self._nodecl = j.clients.osis.getCategory(self._osiscl, 'system', 'node')
        self._jobcl = j.clients.osis.getCategory(self._osiscl, 'system', 'job')
        self._runningnids = list()
        self._nids = list()
        self._nodenames = dict()
        self._nodegids = dict()
        self._errors = dict()
        self._status = dict()
        self._tostdout = True
        with j.logger.nostdout():
            self.getNodes(activecheck=False)

    def _clean(self):
        self._errors = dict()
        self._status = dict()

    def getName(self, id):
        id = int(id)
        if id in self._nodenames:
            return self._nodenames[id]
        else:
            self.getNodes(activecheck=False)
            return self._nodenames.get(id, 'UNKNOWN')

    def getGID(self, id):
        id = int(id)
        if id in self._nodegids:
            return self._nodegids[id]
        else:
            self.getNodes(activecheck=False)
            return self._nodegids.get(id, 'UNKNOWN')

    def _addResult(self, nid, result, category):
        self._status.setdefault(nid, {})
        self._status[nid].setdefault(category, list())
        self._status[nid][category].append(result)

    def _parallelize(self, functionname, clean=False, category=""):
        if functionname.__name__ in ['ping']:
            nodes = self._nids
        else:
            nodes = self._runningnids
        greens = list()
        for nid in nodes:
            greenlet = gevent.Greenlet(functionname, nid, clean)
            greenlet.nid = nid
            greenlet.start()
            greens.append(greenlet)
        gevent.joinall(greens)
        for green in greens:
            result = green.value
            if not result:
                results = [(green.nid, {'message': str(green.exception), 'state': 'UNKNOWN'}, category)]
                self._returnResults(results)

    def _returnResults(self, results):
        for nid, result, category in results:
            self._addResult(nid, result, category)
        return self._status

    def _checkRunningNIDs(self):
        print('CHECKING HEARTBEATS...')
        self._runningnids = list()
        print("\tget all heartbeats (just query from OSIS):")
        heartbeats = self._heartbeatcl.simpleSearch({})
        print("OK")
        for heartbeat in heartbeats:
            if heartbeat['nid'] not in self._nids and  heartbeat['nid']  not in self._nidsNonActive:
                self._addError(heartbeat['nid'],"found heartbeat node '%s' which is not in grid nodes."%(heartbeat['nid']),"heartbeat")

        nid2hb = dict([(x['nid'], x['lastcheck']) for x in heartbeats])
        for nid in self._nids:
            if nid not in self._nidsNonActive:
                if nid in nid2hb:
                    lastchecked = nid2hb[nid]
                    if j.base.time.getEpochAgo('-2m') < lastchecked:
                        # print "%s"%nid,
                        self._runningnids.append(nid)
                    else:                        
                        hago = round(float(j.base.time.getTimeEpoch()-lastchecked)/3600,1)
                        name = self._nodenames[nid]
                        gid = self._nodegids[nid]
                        self._addError(nid, "On node:'%s' (%s) on grid %s. Processmanager is not responding, last heartbeat %s hours ago" % (name, nid, gid, hago), "heartbeat")    
                else:
                    self._addError(nid,"found heartbeat node '%s' which is not in grid nodes." % (nid),"heartbeat")

    def _checkRunningNIDsFromPing(self):
        self._runningnids = self._nids[:]
        for nid, error in list(self._errors.items()):
            for category in error:
                if category == 'processmanagerping':
                    self._runningnids.remove(nid)

    def toStdout(self):
        self._tostdout = True

    def getNodes(self, activecheck=True):
        """
        cache in mem
        list nodes from grid
        list nodes from heartbeat
        if gridnodes found not in heartbeat -> error
        if heartbeat nodes found not in gridnodes -> error
        all the ones found in self._nids (return if populated)
        """
        nodes = self._nodecl.simpleSearch({})
        self._nids = []
        self._nidsNonActive=[]
        for node in nodes:
            self._nodenames[node['id']] = node['name']
            self._nodegids[node['id']] = node['gid']
            if node["active"]==True:
                self._nids.append(node['id'])
            else:
                self._nidsNonActive.append(node['id'])
        if activecheck:
            self.pingAllNodesSync(clean=True)
            self._checkRunningNIDsFromPing()

    def mapJumpscriptsToJobs(self):
        return [(domain, name) for _, domain, name, _ in self._client.listJumpscripts(cat='monitor.healthcheck')]

    def runOnAllNodes(self):
        self._clean()
        self.getNodes()
        self._clean()
        self.checkHeartbeat(clean=False)
        self.checkProcessManagerAllNodes(clean=False)
        results = list()
        greens = list()

        print(('\n**Running tests on %s node(s). %s node(s) have not responded to ping**\n' % (len(self._runningnids), len(self._nids)-len(self._runningnids))))
        nodes = self._runningnids
        for nid in nodes:
            greenlet = gevent.Greenlet(self.runAllOnNode, nid)
            greenlet.start()
            greens.append(greenlet)
            gevent.joinall(greens)
            for green in greens:
                green.nid =nid
                result = green.value
                print result
                if not result:
                    results.append((green.nid, {'message': str(green.exception), 'state': 'UNKNOWN'}, 'Running all healtchecks on node %s' % nid))
                    self._returnResults(results)
        return self._status

    def runAllOnNode(self, nid):
        results = list()
        greens = list()
        for _, domain, name, roles  in self._client.listJumpscripts(cat='monitor.healthcheck'):
            role = roles[0] if roles else None
            greenlet = gevent.Greenlet(self.runOneTest, domain, name, role, nid)
            greenlet.nid = nid
            greenlet.name = name
            greenlet.start()
            greens.append(greenlet)
        gevent.joinall(greens)
        for green in greens:
            greenresults = green.value
            if not greenresults:
                result = (green.nid, {'message': str(green.exception), 'state': 'UNKNOWN'}, green.name)
                results.append(result)
                continue

            if isinstance(greenresults, list):
                for result in greenresults:
                    results.append((green.nid, {'message': result.get('message', ''), 'state': result.get('state', '')}, result.get('category', green.name)))

        self._returnResults(results)
        
        if self._tostdout:
            self._printResults()
        return self._status

    def runOneTest(self, domain, name, role, nid):
        returnedresult = self._client.executeJumpscript(domain, name, role=role, timeout=30, gid=self._nodegids[nid], nid=nid)
        return returnedresult['result']

    def fetchMonitoringOnAllNodes(self):
        self._clean()
        if self._nids==[]:
            self.getNodes()
        for nid in self._nids:
            self.fetchMonitoringOnNode(nid, clean=False)
        return self._status

    def fetchMonitoringOnNode(self, nid, clean=True):
        results = list()
        if clean:
            self._clean()
        self.checkHeartbeat(nid=nid, clean=False)
        self.ping(nid=nid, clean=False)

        maps = self.mapJumpscriptsToJobs()
        domains = [domain for domain, _ in maps]
        names = [name for _, name in maps]
        query = [{'$match': {'nid': nid, 'cmd': {'$in': names}, 'category': {'$in': domains}}},
                 {'$group': {'_id': '$cmd', 'result': {'$last': '$result'}, 
                                            'jobstatus': {'$last': '$state'},
                                            'lastchecked':{'$last': '$timeStop'},
                                            'started':{'$last': '$timeStart'}}}]

        jobsresults = self._jobcl.aggregate(query)

        if isinstance(jobsresults, list):
            for jobresult in jobsresults:
                jobstate = jobresult.get('jobstatus', 'ERROR')
                lastchecked = jobresult.get('lastchecked', 0)
                lastchecked = int(lastchecked) if lastchecked and int(lastchecked) else jobresult.get('started', 0)
                result = json.loads(jobresult.get('result', '[{"message":""}]')) or {}
                if jobstate == 'OK':

                    for data in result:
                        results.append((nid, {'message': data.get('message', ''), 'state': data.get('state', ''), 'lastchecked': lastchecked},
                                        data.get('category', jobresult.get('_id'))))
                    if not result:
                        results.append((nid, {'message': '', 'state': 'UNKNOWN', 'lastchecked': lastchecked}, jobresult.get('_id')))
                else:
                    results.append((nid, {'message': '', 'state': 'UNKNOWN', 'lastchecked': lastchecked}, jobresult.get('_id')))

        self._returnResults(results)

        if self._tostdout:
            self._printResults()
        return self._status

    def _printResults(self):
        form = '%(gid)-8s %(nid)-8s %(name)-10s %(status)-8s %(issues)s'
        print((form % {'gid': 'Grid ID', 'nid': 'NODE ID', 'name': 'NAME', 'status': 'STATUS', 'issues':'ISSUES'}))
        print(('=' * 80))
        print('')
        for nid, checks in list(self._status.items()):
            if nid not in self._errors:
                nodedata={'gid': self.getGID(nid), 'nid': nid, 'name': self.getName(nid), 'status': 'OK', 'issues': ''}
                print((form % nodedata))

        for nid, checks in list(self._errors.items()):
            nodedata={'gid': self.getGID(nid), 'nid': nid, 'name': self.getName(nid), 'status': 'ERROR', 'issues': ''}
            print((form % nodedata))
            for category, errors in list(checks.items()):
                for error in errors:
                    defaultvalue = 'processmanager is unreachable by ping' if category == 'processmanager' else None
                    errormessage = error.get('errormessage', defaultvalue)
                    if errormessage is None:
                        continue
                    for message in errormessage.split(','):
                        nodedata={'gid': '', 'nid': '', 'name': '', 'status': '', 'issues': '- %s' % message}
                        print((form % nodedata))

    def getWikiStatus(self, status):
        colormap = {'RUNNING': 'green', 'HALTED': 'red', 'UNKNOWN': 'orange', 'ERROR': 'red',
                'BROKEN': 'red', 'OK': 'green', 'NOT OK': 'red', 'WARNING': 'orange'}
        return '{color:%s}*%s*{color}' % (colormap.get(status, 'orange'), status)

    def checkProcessManagerAllNodes(self, clean=True):
        if clean:
            self._clean()
        if self._nids==[]:
            self.getNodes()
        print("CHECKING PROCESSMANAGERS...")
        haltednodes = set(self._nids)-set(self._runningnids)
        for nid in haltednodes:
            self._addResult(nid, {'state': 'ERROR'}, 'Processmanager')
        for nid in self._runningnids:
            self._addResult(nid, {'state': 'OK'}, 'Processmanager')
        if clean:
            return self._status


    def checkHeartbeat(self, clean=True, nid=None):
        if clean:
            self._clean()
        if self._nids==[]:
            self.getNodes()
        print('CHECKING HEARTBEATS...')
        print("\tget all heartbeats (just query from OSIS):")
        print("OK")
        query = {}
        if nid:
            query['nid'] = nid
        heartbeats = self._heartbeatcl.simpleSearch(query)
        for heartbeat in heartbeats:
            if heartbeat['nid'] not in self._nids and  heartbeat['nid']  not in self._nidsNonActive:
                self._addResult(heartbeat['nid'], {'message': "Found heartbeat node '%s' when not in grid nodes." % heartbeat['nid'], 
                                'state': 'ERROR'}, "Heartbeat")

        nid2hb = dict([(x['nid'], x['lastcheck']) for x in heartbeats])
        for nid in self._nids:
            if nid not in self._nidsNonActive:
                if nid in nid2hb:
                    lastchecked = nid2hb[nid]
                    hago = j.base.time.getSecondsInHR(j.base.time.getTimeEpoch()-lastchecked)
                    if not j.base.time.getEpochAgo('-2m') < lastchecked:
                        state = 'ERROR'
                    else:
                        state = 'OK'
                    self._addResult(nid, {'message': "*Last heartbeat* %s ago" % hago, 'state': state}, "Heartbeat")
                else:
                    self._addResult(nid, {'message': "Found heartbeat node when not in grid nodes.", 'state':'ERROR'}, "Heartbeat")
        if clean:
            return self._status

    def checkProcessManager(self, nid, clean=True):
        """
        Check heartbeat on specified node, see if result came in osis
        """
        if clean:
            self._clean()
        gid = self.getGID(nid)
        if self._heartbeatcl.exists('%s_%s' % (gid, nid)):
            heartbeat = self._heartbeatcl.get('%s_%s' % (gid, nid))
            lastchecked = heartbeat.lastcheck
            if  j.base.time.getEpochAgo('-2m') < lastchecked:
                self._addResult(nid, {'state': 'RUNNING'}, 'processmanager')
            else:
                self._addError(nid, {'state': 'HALTED'}, 'processmanager')
        else:
            self._addError(nid, {'state': 'UNKNOWN'}, 'processmanager')
        return self._status, self._errors

    def pingAllNodesSync(self, clean=True):
        if clean:
            self._clean()
        if self._nids==[]:
            self.getNodes()
        print(("PROCESS MANAGER PING TO ALL (%s) NODES..." % len(self._nids)))
        self._parallelize(self.ping, False, 'processmanagerping')
        return self._status  

    def ping(self,nid,clean=True):
        if clean:
            self._clean()
        results = list()
        result = self._client.executeJumpscript('jumpscale', 'echo_sync', args={"msg":"ping"}, nid=nid, gid=self._nodegids[nid], timeout=5)
        if not result["result"]=="ping":
            results.append((nid, {'state': 'ERROR', 'message': 'Cannot ping processmanager'}, 'Processmanager'))
        else:
            results.append((nid, {'state': 'OK', 'message': 'Pinging processmanager was successfull'}, 'Processmanager'))
        self._returnResults(results)
        return results

    def checkDBs(self, clean=True):
        if self._nids==[]:
            self.getNodes()
        if clean:
            self._clean()
        errormessage = ''
        nid = j.application.whoAmI.nid
        dbhealth = self._client.executeJumpscript('jumpscale', 'info_gather_db', nid=nid, gid=self._nodegids[nid], timeout=5)
        dbhealth = dbhealth['result']
        if dbhealth == None:
            errormessage = 'Database statuses UNKNOWN'
            self._addResult(nid, {'message': errormessage, 'state': 'UNKNOWN'}, 'databases')
        else:
            for dbname, status in list(dbhealth.items()):
                if status:
                    self._addResult(nid, {'message': '%s is alive' % dbname, 'state': 'OK', 'lastchecked': j.base.time.getTimeEpoch()}, 'databases')
                else:
                    errormessage = '%s status UNKNOWN' % dbname.capitalize()
                    self._addResult(nid, {'message': errormessage, 'state': 'UNKNOWN'}, 'databases')
        if errormessage:
            self._addResult(nid, {'message': errormessage, 'state': 'ERROR'}, 'databases')
        if clean:
            return self._status