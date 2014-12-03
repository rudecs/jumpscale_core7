from JumpScale import j
import ujson
# import urllib.request, urllib.error, urllib.parse

try:
    import urllib
except:
    import urllib.parse as urllib


class RogerthatFactory(object):

    def get(self, api_key):
        return Rogerthat(api_key)

class Rogerthat(object):

    def __init__(self, api_key):
        self._api_key = api_key
        self._url = 'https://rogerth.at/api/1'

    def send_message(self, message, members, flags=0, parent_message_key=None, answers=None, dismiss_button_ui_flags=0, alert_flags=0, branding=None, tag=None, context=None):
        params = {'message': message, 'members': members, 'flags': flags}
        params['parent_message_key'] = parent_message_key
        params['answers'] = answers
        params['dismiss_button_ui_flags'] = dismiss_button_ui_flags
        params['alert_flags'] = alert_flags
        params['branding'] = branding
        params['tag'] = tag
        params['context'] = context

        data = {'id': j.base.idgenerator.generateGUID(), 'method': 'messaging.send', 'params': params}
        json_data = ujson.dumps(data)
        headers = {'Content-Type': 'application/json-rpc; charset=utf-8', 'X-Nuntiuz-API-key': self._api_key}
        request = urllib.request.Request(self._url, json_data, headers)
        response = urllib.request.urlopen(request)
        if response.getcode() == 200:
            result = ujson.loads(response.read())
            return result
        else:
            j.logger.log('Server error when executing send_message')
            return False

