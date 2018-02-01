import urllib
import requests
import string
import random
from JumpScale import j
from jose import jwt as jose_jwt
import datetime
import json


class AuthError(Exception):
    pass


class UserInfo(object):

    def __init__(self, username, emailaddress, groups):
        self.username = username
        self.emailaddress = emailaddress
        self.groups = groups


class OauthInstance(object):

    def __init__(self, addr, accesstokenaddr, id, secret, scope, redirect_url, user_info_url, logout_url, instance):
        if not addr:
            hrd = j.application.getAppInstanceHRD('oauth_client', instance)
            self.addr = hrd.get('instance.oauth.client.url')
            self.accesstokenaddress = hrd.get('instance.oauth.client.url2')
            self.id = hrd.get('instance.oauth.client.id')
            self.scope = hrd.get('instance.oauth.client.scope')
            self.redirect_url = hrd.get('instance.oauth.client.redirect_url')
            self.secret = hrd.get('instance.oauth.client.secret')
            self.user_info_url = hrd.get('instance.oauth.client.user_info_url')
            self.logout_url = hrd.get('instance.oauth.client.logout_url')
        else:
            self.addr = addr
            self.id = id
            self.scope = scope
            self.redirect_url = redirect_url
            self.accesstokenaddress = accesstokenaddr
            self.secret = secret
            self.user_info_url = user_info_url
            self.logout_url = logout_url
        self.state = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(30))

    @property
    def url(self):
        params = {'client_id': self.id, 'redirect_uri': self.redirect_url, 'state': self.state, 'response_type': 'code'}
        if self.scope:
            params.update({'scope': self.scope})
        return '%s?%s' % (self.addr, urllib.urlencode(params))

    def getAccessToken(self, code, state):
        payload = {'code': code, 'client_id': self.id, 'client_secret': self.secret,
                   'redirect_uri': self.redirect_url, 'grant_type': 'authorization_code',
                   'state': state}
        result = requests.post(self.accesstokenaddress, data=payload, headers={
            'Accept': 'application/json'})

        if not result.ok or 'error' in result.json():
            msg = result.json()['error']
            j.logger.log(msg)
            raise AuthError(msg)
        return result.json()

    def getUserInfo(self, accesstoken):
        params = {'access_token': accesstoken['access_token']}
        userinforesp = requests.get('%s?%s' % (self.user_info_url, urllib.urlencode(params)))
        if not userinforesp.ok:
            msg = 'Failed to get user details'
            j.logger.log(msg)
            raise AuthError(msg)

        userinfo = userinforesp.json()
        return UserInfo(userinfo['login'], userinfo['email'], ['user'])

class ItsYouOnline(OauthInstance):

    def extra(self, session, accesstoken):
        jwt = self.getJWT(accesstoken)
        session['jwt'] = jwt
        session.save()

    def getAccessToken(self, code, state):
        payload = {'code': code, 'client_id': self.id, 'client_secret': self.secret,
                   'redirect_uri': self.redirect_url, 'grant_type': '',
                   'state': state}
        result = requests.post(self.accesstokenaddress, data=payload, headers={
            'Accept': 'application/json'})

        if not result.ok or 'error' in result.json():
            msg = result.text
            j.logger.log(msg)
            raise AuthError(msg)
        return result.json()

    def getUserInfo(self, accesstoken):
        headers = {'Authorization': 'token %s' % accesstoken['access_token']}
        scopes = accesstoken['scope'].split(',')
        userinfourl = self.user_info_url.format(**accesstoken.get('info', {}))
        userinforesp = requests.get(userinfourl, headers=headers)
        if not userinforesp.ok:
            msg = 'Failed to get user details'
            j.logger.log(msg)
            raise AuthError(msg)

        groups = ['user']
        for scope in scopes:
            parts = scope.split(':')
            if len(parts) == 3 and parts[:2] == ['user', 'memberof']:
                groups.append(parts[-1].split('.')[-1])

        userinfo = userinforesp.json()
        return UserInfo(userinfo['username'], userinfo['emailaddresses'][0]['emailaddress'], groups)


    def getJWT(self, access_token):
        url = 'https://itsyou.online/v1/oauth/jwt?scope=user:memberof:{0}.0-access,user:publickey:ssh,offline_access'.format(self.id)
        headers = {'Authorization': 'token {0}'.format(access_token['access_token'])}
        resp = requests.get(url, headers=headers)
        jwt = ""
        if resp.status_code == 200:
            jwt = resp.content
        return jwt

    def get_active_jwt(self, jwt=None, session=None):
        """
        Will fetch a new jwt if current jwt is expired
        """
        if not jwt and not session:
            raise RuntimeError("Either jwt or session needs to be set")
        if session:
            jwt = session.get('jwt')
        jwt_data = jose_jwt.get_unverified_claims(jwt)
        jwt_data = json.loads(jwt_data)
        exp_date = datetime.datetime.fromtimestamp(jwt_data["exp"])
        now = datetime.datetime.now()
        if now > exp_date:
            url = 'https://itsyou.online/v1/oauth/jwt/refresh'
            headers = {'Authorization': 'bearer {0}'.format(jwt)}
            resp = requests.get(url, headers=headers)
            jwt = ""
            if resp.status_code == 200:
                jwt = resp.content
                if session:
                    session['jwt'] = jwt
                    session.save()
        return jwt
