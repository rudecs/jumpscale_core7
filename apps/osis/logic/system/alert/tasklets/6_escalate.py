
def main(j, params, service, tags, tasklet):
    """
    Create or update Alert object
    """
    alert = params.value
    alerts_queue = j.clients.redis.getByInstance('system').getQueue('alerts')
    alerts_queue.put(alert['guid'])

def match(j, params, service, tags, tasklet):
    return params.action == 'set'
