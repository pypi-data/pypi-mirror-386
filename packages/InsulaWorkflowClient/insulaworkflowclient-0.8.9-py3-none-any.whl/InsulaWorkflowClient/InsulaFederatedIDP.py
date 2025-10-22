import requests
from time import time
from typing import Optional, Any, Dict, List
from .logger import logger
from .InsulaAuthorizationApiConfig import InsulaAuthorizationApiConfig

from dataclasses import dataclass


@dataclass
class InsulaFederatedIDPConfig(object):
    eoiam_host: Optional[str] = None
    eoiam_client_id: Optional[str] = None
    eoiam_client_secret: Optional[str] = None
    eoiam_uname: Optional[str] = None
    eoiam_password: Optional[str] = None
    eoiam_token:  Optional[str] = None
    esa_maap_kchost: Optional[str] = None
    esa_maap_realm: Optional[str] = None
    esa_maap_client_id: Optional[str] = None
    esa_maap_client_secret: Optional[str] = None
    esa_maap_uname: Optional[str] = None
    esa_maap_password: Optional[str] = None
    disable_ssl: bool = False


class InsulaFederatedIDPConnect(InsulaAuthorizationApiConfig):
    def __init__(self, config_eoian: InsulaFederatedIDPConfig):

        self.__config_eoian = config_eoian
        self.__token_type: str = 'Bearer'

        self.__username: Optional[str] = None
        self.__password: Optional[str] = None

        self.__init_token_time: int = 0
        self.__init_refresh_token_time: int = 0

        self.__refresh_token: Optional[str] = None
        self.__access_token: Optional[str] = None

        self.__expires_in = 0
        self.__refresh_expires_in = 0

        self.__session = requests.Session()
        if self.__config_eoian.disable_ssl:
            self.__session.verify = False

    def get_authorization_header(self):

        if not self.__is_valid_token():
            eoiam_token = None
            if self.__config_eoian.eoiam_token is not None:
                eoiam_token = self.__config_eoian.eoiam_token
            else:
                eoiam_json = self.__create_eoiam_token()
                eoiam_token = eoiam_json['access_token']

            self.__get_esa_token(eoiam_token)

        return f'{self.__token_type} {self.__access_token}'

    def __is_valid_token(self):

        now = time()

        if self.__is_access_token_valid(now):
            logger.debug('use token cache')
            return True

        return False

    def __create_eoiam_token(self) -> Dict[str, Any]:

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "username": self.__config_eoian.eoiam_uname,
            "password": self.__config_eoian.eoiam_password,
            "grant_type": "password",
            "scope": "openid"
        }

        response = self.__session.post(self.__config_eoian.eoiam_host, data=data, headers=headers,
                                       verify=self.__config_eoian.disable_ssl, auth=(self.__config_eoian.eoiam_client_id, self.__config_eoian.eoiam_client_secret))
        if response.status_code != 200:
            self.__logs_and_raise(f'Cannot retrieve token {self.__config_eoian.eoiam_host} [err: {response.status_code}] {response.text}')

        return response.json()

    def __get_esa_token(self, eoiam_access_token: str):

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "requested_subject": self.__config_eoian.esa_maap_uname,
            "client_id": self.__config_eoian.esa_maap_client_id,
            "client_secret":  self.__config_eoian.esa_maap_client_secret,
            "subject_token": eoiam_access_token,
            "subject_issuer": "EOIAM",
            "audience": self.__config_eoian.esa_maap_client_id,
            "scope": "openid"
        }

        url = f"{self.__config_eoian.esa_maap_kchost}/realms/{self.__config_eoian.esa_maap_realm}/protocol/openid-connect/token"
        response = self.__session.post(url, data=data, headers=headers, verify=self.__config_eoian.disable_ssl)

        if response.status_code != 200:
            self.__logs_and_raise(f'Cannot retrieve token {url} [err: {response.status_code}] {response.text}')

        self.__parse_and_update_cache_token(response)

    def __is_access_token_valid(self, now) -> bool:
        return self.__init_token_time + self.__expires_in > now

    def __parse_and_update_cache_token(self, response: requests.Response):
        _token = response.json()
        self.__access_token = _token['access_token']
        # self.__refresh_token = _token['refresh_token']
        self.__token_type = _token['token_type']
        self.__expires_in = _token['expires_in']
        # self.__refresh_expires_in = _token['refresh_expires_in']
        self.__init_token_time = time()
        self.__init_refresh_token_time = time()
        return _token

    @staticmethod
    def __logs_and_raise(msg: str):
        logger.error(msg)
        raise Exception(msg)
