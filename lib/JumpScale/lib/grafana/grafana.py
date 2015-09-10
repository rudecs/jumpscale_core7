import requests
import os

class GrafanaFactory(object):
    def get(self):
        return GrafanaClient("http://admin:admin@localhost:3000")

class GrafanaClient(object):
    def __init__(self, apiurl):
        self._url = apiurl

    def updateDashboard(self, dashboard):
        url = os.path.join(self._url, 'api/dashboards/db')
        data = {'dashboard': dashboard, 'overwrite': True}
        result = requests.post(url, json=data)
        return result.json()

    def listDashBoards(self):
        url = os.path.join(self._url, 'api/search/')
        return requests.get(url).json()

    def delete(self, dashboard):
        url = os.path.join(self._url, 'api/dashboards', dashboard['uri'])
        return requests.delete(url)

