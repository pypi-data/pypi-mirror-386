# coding:utf-8
import json
import threading

from byteplus_sdk.ApiInfo import ApiInfo
from byteplus_sdk.Credentials import Credentials
from byteplus_sdk.base.Service import Service
from byteplus_sdk.ServiceInfo import ServiceInfo


class IamService(Service):
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not hasattr(IamService, "_instance"):
            with IamService._instance_lock:
                if not hasattr(IamService, "_instance"):
                    IamService._instance = object.__new__(cls)
        return IamService._instance

    def __init__(self):
        self.service_info = IamService.get_service_info()
        self.api_info = IamService.get_api_info()
        super(IamService, self).__init__(self.service_info, self.api_info)

    @staticmethod
    def get_service_info():
        service_info = ServiceInfo("open.byteplusapi.com", {'Accept': 'application/json'},
                                   Credentials('', '', 'iam', 'ap-singapore-1'), 5, 5)
        return service_info

    @staticmethod
    def get_api_info():
        api_info = {"ListUsers": ApiInfo("GET", "/", {"Action": "ListUsers", "Version": "2018-01-01"}, {}, {})}
        return api_info

    def list_users(self, params):
        res = self.get("ListUsers", params)
        if res == '':
            raise Exception("empty response")
        res_json = json.loads(res)
        return res_json
