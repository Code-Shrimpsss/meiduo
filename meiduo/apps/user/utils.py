from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as TimeSerializer, BadData
from django.conf import settings
from apps.user.models import User

# 加密
def generate_verify_email_url(user):
    """
    生成邮箱验证链接
    :param user: 当前登录用户
    :return: verify_url
    """
    serializer = TimeSerializer(settings.SECRET_KEY, expires_in=600)
    data = {'user_id': user.id}
    token = serializer.dumps(data).decode()
    verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token
    return verify_url

# 解密
def check_verify_email_token(token):
    """
    验证token并提取user
    :param token: 用户信息签名后的结果
    :return: user, None
    """
    serializer = Serializer(settings.SECRET_KEY, expires_in=600)
    try:
        data = serializer.loads(token)
    except BadData:
        return None
    else:
        user_id = data.get('user_id')
        return user_id
