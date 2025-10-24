#  -*- coding: utf-8 -*-
import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../../../")
from volcengine.example.cdn import ak, sk
from volcengine.cdn.service import CDNService

if __name__ == '__main__':
    svc = CDNService()
    svc.set_ak(ak)
    svc.set_sk(sk)
    print(ak, sk)
    body = {
        "Type": "file",
        "Urls": "http://example.com/1.txt\nhttp://example.com/2.jpg",
    }

    resp = svc.submit_refresh_task(body)
    print(resp)
