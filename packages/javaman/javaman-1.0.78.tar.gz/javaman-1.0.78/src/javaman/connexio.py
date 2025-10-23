import json
import requests
from .errors import *



class ConfigJavaman:
    __slots__ = '_config'

    def __init__(self, config_data: dict):
        self._config = config_data

    def url(self):
        return self._config["url"]

    def instancia_guid(self):
        return self._config["instancia_guid"]

    def empresa_guid(self):
        return self._config["empresa_guid"]

    def usuari_manager(self):
        return self._config["usuari_manager"]

    def password_manager(self):
        return self._config["password_manager"]

    def maquina_manager(self):
        return self._config["maquina_manager"]


class JManCon:
    __slots__ = '_usuari_token', '_config'

    def __init__(self, config_data: dict):
        self._config = ConfigJavaman(config_data=config_data)
        data = {
            "user_login": self._config.usuari_manager(),
            "user_password": self._config.password_manager(),
            "instancia_guid": self._config.instancia_guid(),
            "empresa_guid": self._config.empresa_guid()
        }
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }
        req = requests.post(url=self._config.url() + '/login/usuari', headers=headers, data=json.dumps(data))
        if req.status_code not in [200, 201]:
            raise JManErrorUnauthorized()
        self._usuari_token = req.json()['token']

    @property
    def config(self) -> ConfigJavaman:
        return self._config

    @property
    def usuari_token(self) -> str:
        return self._usuari_token

    def post(self, url: str, data: [list, dict] = None) -> requests:
        headers = {
            'Accept': 'application/json',
            'authorization': "Bearer " + self.usuari_token
        }
        if data is not None:
            headers['Content-type'] = 'application/json'
        if data is not None:
            data = json.dumps(data)
        req = None
        try:
            req = requests.post(url=self._config.url() + url, headers=headers, data=data)
        except requests.exceptions.RequestException:
            raise JManErrorConnection(req.content)
        if req.status_code < 200 or 300 <= req.status_code < 400:
            raise JManErrorConnection(req.content)
        if req.status_code < 200 or req.status_code >= 500:
            raise JManErrorApp(req.content)
        if 400 <= req.status_code < 500:
            raise JManErrorClient(req.content)
        return req

    def put(self, url: str, data: [list, dict, None]) -> requests:
        headers = {
            'Accept': 'application/json',
            'authorization': "Bearer " + self.usuari_token
        }
        if data is not None:
            headers['Content-type'] = 'application/json'
        if data is not None:
            data = json.dumps(data)
        req = None
        try:
            req = requests.put(url=self._config.url() + url, headers=headers, data=data)
        except requests.exceptions.RequestException:
            raise JManErrorConnection(req.content)
        if req.status_code < 200 or 300 <= req.status_code < 400:
            raise JManErrorConnection(req.content)
        if req.status_code < 200 or req.status_code >= 500:
            raise JManErrorApp(req.content)
        if 400 <= req.status_code < 500:
            raise JManErrorClient(req.content)
        return req

    def get(self, url: str) -> requests:
        headers = {
            'Accept': 'application/json',
            'authorization': "Bearer " + self.usuari_token
        }
        req = None
        try:
            req = requests.get(url=self._config.url() + url, headers=headers)
        except requests.exceptions.RequestException:
            raise JManErrorConnection(req.content)
        if req.status_code < 200 or 300 <= req.status_code < 400:
            raise JManErrorConnection(req.content)
        if req.status_code < 200 or req.status_code >= 500:
            raise JManErrorApp(req.content)
        if 400 <= req.status_code < 500:
            raise JManErrorClient(req.content)
        return req

    def delete(self, url: str) -> requests:
        headers = {'authorization': "Bearer " + self.usuari_token}
        req = None
        try:
            req = requests.delete(url=self._config.url() + url, headers=headers)
        except requests.exceptions.RequestException:
            raise JManErrorConnection(req.content)
        if req.status_code < 200 or 300 <= req.status_code < 400:
            raise JManErrorConnection(req.content)
        if req.status_code < 200 or req.status_code >= 500:
            raise JManErrorApp(req.content)
        if 400 <= req.status_code < 500:
            raise JManErrorClient(req.content)
        return req

    def __del__(self):
        self.delete(url='/logout')
