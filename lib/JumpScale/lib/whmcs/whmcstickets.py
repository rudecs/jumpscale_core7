from JumpScale import j
import requests, base64, phpserialize
from settings import authenticationparams, WHMCS_API_ENDPOINT, OPERATIONS_USER_ID, MOTHERSHIP1_OPERATIONS_DEPARTMENT_ID
import json
import xml.etree.cElementTree as et


class whmcstickets():
    def __init__(self):
        pass

    def _call_whmcs_api(self, requestparams):
        actualrequestparams = dict()
        actualrequestparams.update(requestparams)
        actualrequestparams.update(authenticationparams)
        response = requests.post(WHMCS_API_ENDPOINT, data=actualrequestparams)
        return response

    def list_deps(self):        
        params = dict(action='getsupportdepartments')
        response = self._call_whmcs_api(params)
        result = dict((attr.tag, attr.text) for attr in et.fromstring(response.content))
        return result

    def create_ticket(self, subject, message, priority, clientid=OPERATIONS_USER_ID, deptid=MOTHERSHIP1_OPERATIONS_DEPARTMENT_ID):
        print 'Creating %s' % subject
        create_ticket_request_params = dict(

                    action = 'openticket',
                    responsetype = 'json',
                    clientid = clientid,
                    subject = subject,
                    deptid = deptid,
                    message = message,
                    priority = priority,
                    noemail = True,
                    skipvalidation= True
                    )
        
        response = self._call_whmcs_api(create_ticket_request_params)
        content = json.loads(response.content)
        ticketid = content.get('id', None)
        if not ticketid:
            j.events.opserror_critical('Failed to create ticket. Error: %s' % response.content, category='whmcs')
        return ticketid


    def update_ticket(self, ticketid, subject=None, priority=None, status=None, email=None, cc=None, flag=None, userid=OPERATIONS_USER_ID, deptid=MOTHERSHIP1_OPERATIONS_DEPARTMENT_ID):
        print 'Updating %s' % ticketid
        ticket_request_params = dict()

        ticket_request_params['action'] = 'updateclient'
        ticket_request_params['responsetype'] = 'json'
        ticket_request_params['ticketid'] = ticketid
        if deptid:
            ticket_request_params['deptid'] = deptid
        if subject:
            ticket_request_params['subject'] = subject
        if priority:
            ticket_request_params['priority'] = priority
        if status:
            ticket_request_params['status'] = status
        if userid:
            ticket_request_params['userid'] = None
        ticket_request_params['noemail'] = True
        ticket_request_params['skipvalidation'] = True
        
        response = self._call_whmcs_api(ticket_request_params)
        content = json.loads(response.content)
        if content.pop('result') == 'error':
            j.events.opserror_warning('Failed to update ticket %s. Error: %s' % (ticketid, response.content), category='whmcs')
        return response

    def close_ticket(self, ticketid):
        print 'Closing %s' % ticketid
        ticket_request_params = dict(

                    action = 'updateclient',
                    responsetype = 'json',
                    ticketid = ticketid,
                    status = 'Closed',
                    noemail = True,
                    skipvalidation= True

                    )
        
        response = self._call_whmcs_api(ticket_request_params)
        content = json.loads(response.content)
        if content.pop('result') == 'error':
            j.events.opserror_warning('Failed to close ticket %s. Error: %s' % (ticketid, response.content), category='whmcs')
        return response.ok


    def get_ticket(self, ticketid):
        print 'Getting %s' % ticketid
        ticket_request_params = dict(

                    action = 'getticket',
                    ticketid = ticketid,
                    )
        xs = self._call_whmcs_api(ticket_request_params).content
        if json.loads(xs).get('result') == 'error':
            j.events.opserror_warning('Failed to get ticket %s. Error: %s' % (ticketid, xs), category='whmcs')
        ticket = dict((attr.tag, attr.text) for attr in et.fromstring(xs))
        return ticket

    def add_note(self, ticketid, message):
        print "Adding note to ticket %s" % ticketid
        ticket_request_params = dict(
            action = 'addticketnote',
            ticketid = ticketid,
            message = message
            )

        response = self._call_whmcs_api(ticket_request_params)
        content = json.loads(response.content)
        if content.pop('result') == 'error':
            j.events.opserror_warning('Failed to add note to ticket %s. Error: %s' % (ticketid, response.content), category='whmcs')
        return response.ok



