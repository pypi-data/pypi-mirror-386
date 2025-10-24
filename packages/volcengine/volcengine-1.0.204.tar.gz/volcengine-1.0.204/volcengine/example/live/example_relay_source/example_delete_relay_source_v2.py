# coding:utf-8
import json

from volcengine.live.LiveService import LiveService
from volcengine.live.models.request.request_live_pb2 import DeleteRelaySourceRequest

if __name__ == '__main__':
    live_service = LiveService()
    live_service.set_ak('')
    live_service.set_sk('')
    req = DeleteRelaySourceRequest()
    req.Vhost = 'Vhost'
    req.App = 'App'
    print(req)
    resp = live_service.delete_relay_source_v2(req)
    print(resp)

