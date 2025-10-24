#  -*- coding: utf-8 -*-
import os
import sys
import datetime 

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../../../")

from byteplus_sdk.example.cdn import ak, sk
from byteplus_sdk.cdn.service import CDNService

if __name__ == '__main__':
    svc = CDNService()
    svc.set_ak(ak)
    svc.set_sk(sk)

    now = int(datetime.datetime.now().strftime("%s"))
    body = {
        'StartTime': now - 600,
        'EndTime': now,
        'Metric': 'flux',
        'Domain': 'example.com',
    }

    resp = svc.describe_cdn_data_detail(body)
    print(resp)
