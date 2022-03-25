import json
from ronglian_sms_sdk import SmsSDK


class SmsUtils:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls, *args, **kwargs)
            cls.smsSdk = SmsSDK(accId='8aaf07087dc23905017dc78bdab701f8', accToken='37029ad43ffd4fc78b3689a6e54136e8',
                                appId='8aaf07087dc23905017dc78bdbca01ff')
        return cls.__instance

    def send_message(self, mobile='18031811527', tid='1', code='1234'):
        sendback = self.smsSdk.sendMessage(tid=tid, mobile=mobile, datas=(code, 5))
        # 把返回值转为字典
        sendback = json.loads(sendback)
        if sendback.get('statusCode') == '000000':
            print('发送成功')
        else:
            print('发送失败')
