import json
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django_redis import get_redis_connection
from redis import Redis
from apps.user.utils import generate_verify_email_url, check_verify_email_token
from celery_tasks.email.tasks import send_email_active
from apps.user.models import User
from django import http
import re


# 用户名重复
class UsernameCountView(View):
    def get(self, request, username):
        """
        :param request: 请求对象
        :param username: 用户名
        :return: JSON
        """
        # 1.接收用户名
        print(username)
        try:
            # 2.根据用户名查询数据库，查询数量有几个
            count = User.objects.filter(username=username).count()
        except Exception as e:
            print(e)
            return JsonResponse({'count': '15', 'errmsg': 'OK'})
        print('count=', count)
        # 3.返回json数据
        return JsonResponse({'count': count, 'code': '0', 'errmsg': 'OK'})


# 手机号重复
class MobileCountView(View):
    def get(self, request, mobile):
        """
        :param request: 请求对象
        :param mobile: 手机号
        :return: JSON
        """
        print(mobile)
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            print(e)
            return JsonResponse({'count': '15', 'errmsg': 'OK'})
        print('count=', count)
        return JsonResponse({'count': count, 'code': '0', 'errmsg': 'OK'})


# 用户注册
class RegisterView(View):
    def post(self, request):
        body_byte = request.body
        data_dict = json.loads(body_byte)
        print(data_dict)
        username = data_dict.get('username')
        print(username)
        password = data_dict.get('password')
        print(password)
        password2 = data_dict.get('password2')
        print(password2)
        mobile = data_dict.get('mobile')
        print(mobile)
        allow = data_dict.get('allow')
        sms_code = data_dict.get('sms_code')
        if not all([username, password, password2, mobile, allow]):
            return http.JsonResponse({'code': 400, 'errmsg': '缺少必传参数!'})
        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_]{5,20}$', username):
            return http.JsonResponse({'code': 400, 'errmsg': 'username格式有误!'})
        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.JsonResponse({'code': 400, 'errmsg': 'password格式有误!'})
        # 判断两次密码是否一致
        if password != password2:
            return http.JsonResponse({'code': 400, 'errmsg': '两次输入不对!'})
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400, 'errmsg': 'mobile格式有误!'})
        # 判断是否勾选用户协议
        if allow != True:
            return http.JsonResponse({'code': 400, 'errmsg': 'allow格式有误!'})
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except Exception as e:
            return http.JsonResponse({'code': 400, 'errmsg': '注册失败!'})
        login(request, user)

        # 判断短信验证是否正确
        # 1. 从redis取短信验证码 不要忘记decode
        redis: Redis = get_redis_connection('code')
        sms_code_redis = redis.get('smscode_%s' % mobile)
        # 2.如果没取到说明过期 ，返回错误
        if not sms_code_redis:
            return JsonResponse({'code': 400, 'errmsg': '验证码过期'})
        # 3.和用户发来的对比
        sms_code_redis = sms_code_redis.decode()
        if sms_code != sms_code_redis:
            return JsonResponse({'code': 400, 'errmsg': '验证码过期'})

        return http.JsonResponse({'code': 0, 'errmsg': '注册成功!'})


class LoginView(View):
    def post(self, request):
        # 1.接收参数
        body = request.body
        data_dict = json.loads(body)
        username = data_dict.get('username')
        password = data_dict.get('password')
        remembered = data_dict.get('remembered')
        # 2.验证数据是否为空
        if not all([username, password, remembered]):
            return JsonResponse({'code': 400, 'errmsg': '用户名和密码'})
        # 3.正则判断是不是手机号（多账号登录）
        if re.match('^1[3-9]\d{9}$', username):
            # 手机号
            User.USERNAME_FIELD = 'mobile'
        else:
            # 根据用户名从数据库获取 user 对象返回.
            User.USERNAME_FIELD = 'username'
        # 4.验证码用户名和密码是否正确
        user = authenticate(username=username, password=password)
        if not user:
            return JsonResponse({'code': '400', 'errmsg': '用户名和密码'})
        # 5.状态保持
        login(request, user)
        # 6.判断是否记住登录
        if remembered:
            # 如果记住：设置为两周有效
            request.session.set_expiry(None)
        else:
            # 如果没有记住：关闭立刻失效
            request.session.set_expiry(0)
        # 7.返回响应
        response = JsonResponse({'code': 0, 'errmsg': 'OK'})
        # 8.注册是用户名写入到cookie，有效期15天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        return response


# 用户名登录
# class LoginView(View):
#     def post(self, request):
#         # 1.接收参数
#         body = request.body
#         data_dict = json.loads(body)
#         username = data_dict.get('username')
#         password = data_dict.get('password')
#         remembered = data_dict.get('remembered')
#         # 2.验证数据是否为空 正则
#         if not all([username, password, remembered]):
#             return JsonResponse({'code': 400, 'errmsg': '用户名和密码写错了'})
#         # 3.正则判断是不是手机号
#         if re.match('^1[3-9]\d{9}$', username):
#             # 手机号
#             User.USERNAME_FIELD = 'mobile'
#         else:
#             # account 是用户名
#             # 根据用户名从数据库获取 user 对象返回.
#             User.USERNAME_FIELD = 'username'
#         # 3.验证码用户名和密码是否正确
#         user = authenticate(username=username, password=password)
#         if not user:
#             return JsonResponse({'code': 400, 'errmsg': '用户名密码错误'})
#         # 4.状态保持
#         login(request, user)
#         # 5.判断是否记住登录
#         if remembered:
#             # 如果记住：设置为两周有效
#             request.session.set_expiry(None)
#         else:
#             # 如果没有记住：关闭立刻失效
#             request.session.set_expiry(0)
#         # 6.返回响应
#         response = JsonResponse({"code": 0, "errmsg": 'OK'})
#         # 注册是用户名写入到cookie，有效期15天
#         response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
#         return response

# 退出登录
class LogoutView(View):
    def delete(self, request):
        # 实现退出登录
        # 清理session
        logout(request)
        # 退出登录，重定向到登录页面
        response = JsonResponse({'code': 0, "errmsg": 'OK'})
        # 退出登录时清除cookie中的username
        response.delete_cookie('username')
        return response


# 用户中心
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        print(request.user.email)
        print(request.user.email_active)
        print(request.user.mobile)
        return http.JsonResponse({'code': 0, 'errmsg': '个人中心', 'info_data': {'username': request.user.username,
                                                                             'mobile': request.user.mobile,
                                                                             'email': request.user.email,
                                                                             'email_active': request.user.email_active}})


# 邮箱
class SaveEmailView(LoginRequiredMixin, View):
    def put(self, request):
        # 1.获取json数据转为字典
        body = request.body
        data_dict = json.loads(body)
        # 2.从字典里拿到邮箱地址
        email = data_dict.get('email')
        # 3.校验
        if not email:
            return JsonResponse({'code': 300, 'errmsg': '邮箱不存在'})
        # 4.保存到数据库
        try:
            request.user.email = email
            print(request.user.email)
            request.user.save()
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '邮箱保存失败'})
        verify_url = generate_verify_email_url(request.user)
        message = '<p>尊敬的用户您好！</p><p>感谢您使用美多商城。</p>' \
                  '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                  '<p>< a href="%s">点我激活<a></p>' % (email, verify_url)
        # 同步发送邮件
        send_email_active(email, message)
        # 异步发送邮件(window不支持celery)
        # send_email_active.delay(email, message)
        # 5.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'OK'})


# 邮箱激活
class EmailVerifyView(View):
    # 1.接收请求（put）数据
    def put(self, request):
        # 2.获取token
        token = request.GET.get('token')
        # token是否存在
        if not token:
            return JsonResponse({'code': 400, 'errmsg': 'token缺少'})
        # 3.对token进行解密 获取解密数据里面的user_id
        user_id = check_verify_email_token(token)
        print(user_id)
        # 4. 如果获取不到说明过期
        if not user_id:
            return JsonResponse({'code': 400, 'errmsg': '激活邮件已经过期'})
        # 5.根据user_id去数据库查询
        try:
            user = User.objects.get(id=user_id)
            print(user)
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '当前用户不存在'})
        # 6.把查到的user对象的email_active字段给为true 不要忘记save
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '激活失败'})

        return JsonResponse({'code': 0, 'errmsg': '激活成功'})


# 修改密码
class ChangePasswordView(View):
    def put(self, request):
        # 接收参数
        body = request.body
        data_dict = json.loads(body)
        old_password = data_dict.get('old_password')
        print(old_password)
        new_password = data_dict.get('new_password')
        print(new_password)
        new_password2 = data_dict.get('new_password2')
        print(new_password2)
        if not all([old_password, new_password, new_password2]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        result = request.user.check_password((old_password))
        if not result:
            return JsonResponse({'code': 400, 'errmsg': '原始密码不对'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return JsonResponse({'code': 400, 'errmsg': '密码最少8位，最长20位'})
        if new_password != new_password2:
            return JsonResponse({"code": 400, 'errmsg': '两次密码不一致'})
        # 修改密码
        try:
            request.user.set_password((new_password))
            request.user.save()
        except Exception as e:
            print(e)
            return JsonResponse({"code": 400, 'errmsg': '修改密码失败'})
        # 清空状态保持信息
        logout(request)
        response = JsonResponse({'code': 0, 'errmsg': 'OK'})
        response.delete_cookie('username')
        return response
