#  -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/../../../")
import datetime

from byteplus_sdk.example.cdn import ak, sk
from byteplus_sdk.cdn.service import CDNService

if __name__ == '__main__':
    svc = CDNService()
    svc.set_ak(ak)
    svc.set_sk(sk)
    now = int(datetime.datetime.now().strftime("%s"))
    body = {
        'TaskType': 'block_url',
        'StartTime': now - 86400,
        'EndTime': now,
    }
    print(body)

    resp = svc.describe_content_block_tasks(body)
    print(resp)
