import random
from django.http import HttpResponse, JsonResponse
from django.views import View
from django_redis import get_redis_connection
from redis import Redis
from celery_tasks.sms.tasks import send_sms_code
from libs.captcha.captcha import captcha


# 图形验证码
class ImageCodeView(View):
    def get(self, request, uuid):
        """
        :param request: 请求对象
        :param uuid: 唯一标识图形验证码所属于的用户
        :return: image/jpeg
        """
        # 生成图片验证码
        text, image = captcha.generate_captcha()
        print(text)
        # 保存图片验证
        redis_conn = get_redis_connection('code')
        print(redis_conn)
        redis_conn.setex(uuid, 300, text)
        # 响应图片验证
        return HttpResponse(image, content_type='image/jpeg')


# 短信验证码
class SmsView(View):
    def get(self, request, mobile):
        # 校验手机号格式是否正确
        if not mobile:
            return JsonResponse({'code': 300, 'errmsg': '手机号为空'})
        # 正则验证
        # 校验图片验证码是否正确
        # 用户发过来的验证码image_code
        image_code: str = request.GET.get('image_code')
        print('image_code', image_code)
        image_code_uuid = request.GET.get('image_code_id')
        try:
            # 获取保存都在redis里的图片验证码
            redis: Redis = get_redis_connection('code')
            print(redis)
            image_code_redis = redis.get(image_code_uuid)
            if not image_code_redis:
                return JsonResponse({'code': 400, "errmsg": "验证码过期"})
            image_code_redis = image_code_redis.decode()
            print('image_code_redis', image_code_redis)
            if image_code.lower() != image_code_redis.lower():
                return JsonResponse({'code': 500, 'errmsg': '图形验证码错误'})
        except Exception as e:
            print(e)
            return JsonResponse({'code': 600, "errmsg": "网络异常"})
        # 给手机号发送短信 第三方
        print('发送短信', mobile)
        # 先根据key : flag_手机号,获取值
        flag_send = redis.get('flag_%s' % mobile)
        # 2.如果值存在，返回错误响应，过于请求频繁
        if flag_send:
            return JsonResponse({'code': 110, 'errmsg': '短信已经发送，清稍后重试'})
        # 3.如果不存在就可以继续发送短信验证码
        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        print(sms_code)
        # sdk = SmsSDK(accId='8aaf07087dc23905017dc78bdab701f8', accToken='37029ad43ffd4fc78b3689a6e54136e8',
        #              appId='8aaf07087dc23905017dc78bdbca01ff')
        # sdk.sendMessage(tid='1', mobile='18031811527', datas=('1234', 5))
        # 同步
        # SmsUtils().send_message(mobile=mobile, code=sms_code)
        # 异步
        send_sms_code(mobile, code=sms_code)

        pipline = redis.pipeline()
        pipline.setex('smscode_%s' % mobile, 60 * 3, sms_code)

        # 4.发送完保存 flag_手机号  value：1 有效期 60秒（和前端倒计时一样）
        pipline.setex('flag_%s' % mobile, 120, 1)
        pipline.execute()
        return JsonResponse({'code': 0, "errmsg": 'OK'})
