# -*- coding: utf-8 -*-

import requests
import json

class SMSService(object):
    authorization_key = 'Basic eXRldmlldGFuaF9hcGk6MTIzZTMxNHZxenhxYQ=='
    brand_name = 'DHA Medic'
    api_url = 'https://api-01.worldsms.vn/webapi/sendMTSMS'

    def send_sms(self, to, content):
        if to[0] == '0':
            to = "84" + to[1:]
        elif to[0] == '+':
            to = to[1:]

        data = {
            "from": self.brand_name,
            "to": to,
            "text": content
        }

        headers = {
            'Authorization': self.authorization_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        raw = requests.post(self.api_url, data=json.dumps(data), headers=headers)
        return raw.json()
