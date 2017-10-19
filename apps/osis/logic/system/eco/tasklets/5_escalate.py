cache = {}
nodes_cache = {}

def main(j, params, service, tags, tasklet):
    """
    Create or update Alert object
    """

    """
    Define alerta information in system/system.hrd

alerta.api_key                 = 'j4ypz80lnQMHC3Ah8jiatrcfPP2ktWJdgW18UlpE'
alerta.api_url                 = 'http://172.17.0.3:8080'


For operator

export ALERTA_SVR_CONF_FILE=~/.alertad.conf

root@js7:~cat ~/.alertad.conf
DEBUG = True
CORS_ORIGINS = [
        '*',
        'http://172.17.0.3:8000',
        'http://172.17.0.3:8080',

]

SEVERITY_MAP = {
         'CRITICAL':1,
         'WARNING': 2,
         'INFO':3,
         'DEBUG':4
}


ALLOWED_ENVIRONMENTS = ["du-conv-2", "production"]

    """

    from JumpScale import j
    import requests

    config = j.application.config.getDictFromPrefix("system.alerta")

    if not config:
        return

    eco = params.value
    gid, nid = eco['gid'], eco['nid']
    if gid not in cache:
        gridservice = j.core.osis.cmds._getOsisInstanceForCat('system', 'grid')
        grids = gridservice.search({'id':gid})[1:]
        if grids:
            cache[gid] = grids[0]['name']
        else:
            cache[gid] = "Development"

    if nid not in nodes_cache:
        nodeservice = j.core.osis.cmds._getOsisInstanceForCat('system', 'node')
        nodes = nodeservice.search({'id': nid})[1:]
        if nodes:
            nodes_cache[nid] = nodes[0]['name']
        else:
            nodes_cache[nid] = "Unrecognized Node"
        

    envname = cache[gid]
    node = nodes_cache[nid]
    backtrace = eco['backtrace']
    tags = "gid:{},nid:{}".format(gid, nid)


    headers = {
                "Authorization": "Key {}".format(config['api_key']),
                "Content-type": "application/json"
              }


    severity = j.errorconditionhandler.getLevelName(eco['level'])
    data = dict(attributes={'backtrace': backtrace}, resource=eco['guid'],
                text=eco['errormessage'], environment=envname, service=["{} - {}".format(node, eco['appname'])],
                tags=[tags], severity=severity, event="ErrorCondition")
    if eco['state'].lower() == "closed":
        data['status'] = "closed"
        
    try:
        resp = requests.post(config['api_url']+"/alert", json=data, headers=headers)
        if resp.status_code != 201:
            print('Can not send Alert code: {}, resp: {}'.format(resp.status_code, resp.text))
    except Exception as e:
        print(e)


def match(j, params, service, tags, tasklet):

    eco = params.value

    return params.action == 'set'
