import requests
import time

try:
    import ujson as json
except:
    import json

def main():
    response = requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/fw.list?&gid=1')
    response = str(response.content, 'iso-8859-1')
    result = json.loads(response)
    if not isinstance(result, list):
        print('ERROR: FW listing failed')
    else:
        print('FW listing success.')
    length = len(result)

    created_fwid = None
    response = requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/fw.create?masquerade=False&domain=testdomain&gid=1&name=testFW&nid=1')
    response = str(response.content, 'iso-8859-1')
    result = json.loads(response)
    if not isinstance(result, str):
        print('ERROR: FW Creation failed')
    else:
        print('FW creation success. FW ID = %s' % result)
        created_fwid = result

    response = requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/fw.list?&gid=1')
    response = str(response.content, 'iso-8859-1')
    result = json.loads(response)
    if not isinstance(result, list):
        print('ERROR: FW listing failed')
    if len(result) != length + 1:
        print('FW creation was unsuccessful')

    time.sleep(1)
    if created_fwid:
        requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/fw.delete?gid=1&fwid=%s' % created_fwid)
        response = requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/fw.list?&gid=1')
        response = str(response.content, 'iso-8859-1')
        result = json.loads(response)
        if not isinstance(result, list):
            print('ERROR: FW listing failed')
        if len(result) != length:
            print('FW deletion was unsuccessful')
        else:
            print('FW deletion was successful')

    created_fwid = None
    response = requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/fw.create?masquerade=False&domain=testdomain&gid=1&name=testFW&nid=1')
    response = str(response.content, 'iso-8859-1')
    result = json.loads(response)
    if not isinstance(result, str):
        print('ERROR: FW second creation failed')
    else:
        print('FW creation success. FW ID = %s' % result)
        created_fwid = result


    #### FW Forward ####

    response = requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/fw.forward.list?&gid=1&fwid=%s' % created_fwid)
    response = str(response.content, 'iso-8859-1')
    result = json.loads(response)
    if not isinstance(result, list):
        print('ERROR: FW Forward listing failed')
    else:
        print('FW Forward listing success.')
    fwf_length = len(result)

    response = requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/fw.forward.create?destip=127.0.0.1&destport=80&fwport=8080&gid=1&fwid=%s' % created_fwid)
    response = str(response.content, 'iso-8859-1')
    result = json.loads(response)
    if not result:
        print('ERROR: FW forward creation failed')
    else:
        print('FW forward creation success.')

    response = requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/fw.forward.list?&gid=1&fwid=%s' % created_fwid)
    response = str(response.content, 'iso-8859-1')
    result = json.loads(response)
    if not isinstance(result, list):
        print('ERROR: FW forward listing failed')
    else:
        print('FW listing forward success.')
    if len(result) != fwf_length + 1:
        print('ERROR: FW forward creation was unsuccessful')

    requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/fw.forward.delete?destip=127.0.0.1&destport=80&fwport=8080&gid=1&fwid=%s' % created_fwid)
    response = requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/fw.forward.list?&gid=1&fwid=%s' % created_fwid)
    response = str(response.content, 'iso-8859-1')
    result = json.loads(response)
    if not isinstance(result, list):
        print('ERROR: FW forwarad listing failed')
    if len(result) != fwf_length:
        print('FW forward deletion was unsuccessful')
    else:
        print('FW forward deletion was successful')


    #### WS Forward ####

    response = requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/ws.forward.list?&gid=1&wsid=%s' % created_fwid)
    response = str(response.content, 'iso-8859-1')
    result = json.loads(response)
    if not isinstance(result, list):
        print('ERROR: WS Forward listing failed')
    else:
        print('WS Forward listing success.')
    wsf_length = len(result)

    response = requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/ws.forward.create?sourceurl=google.com&desturls=a,b&gid=1&wsid=%s' % created_fwid)
    response = str(response.content, 'iso-8859-1')
    result = json.loads(response)
    if not result:
        print('ERROR: WS forward creation failed')
    else:
        print('WS forward creation success.')

    response = requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/ws.forward.list?&gid=1&wsid=%s' % created_fwid)
    response = str(response.content, 'iso-8859-1')
    result = json.loads(response)
    if not isinstance(result, list):
        print('ERROR: WS forward listing failed')
    if len(result) != wsf_length + 1:
        print('WS forward creation was unsuccessful')
    else:
        print('WS forward creation was successful')

    requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/ws.forward.delete?sourceurl=google.com&desturls=a,b&gid=1&wsid=%s' % created_fwid)
    response = requests.get('http://95.85.60.252:81/restmachine/jumpscale/netmgr/ws.forward.list?&gid=1&wsid=%s' % created_fwid)
    response = str(response.content, 'iso-8859-1')
    result = json.loads(response)
    if not isinstance(result, list):
        print('ERROR: WS forwarad listing failed')
    if len(result) != wsf_length:
        print('WS forward deletion was unsuccessful')
    else:
        print('WS forward deletion was successful')



if  __name__ =='__main__':main()
