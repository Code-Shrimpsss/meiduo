from itsdangerous import BadData
from itsdangerous import TimedJSONWebSignatureSerializer as TimeSerializer
from django.conf import settings

# 加密
def generate_access_token(token):
    """
    签名微博token
    :param 微博token: 用户的微博token
    :return: access_token
    """
    # 盐值 settings.SECRET_KEY
    serializer = TimeSerializer(settings.SECRET_KEY, expires_in=3600)
    data = {'token': token}
    token = serializer.dumps(data)
    return token.decode()

# 解密
def check_access_token(token_sign):
    """
    提取微博token
    :param token_sign: 签名后的token
    :return: openid or None
    """
    serializer = TimeSerializer(settings.SECRET_KEY, expires_in=3600)
    try:
        data = serializer.loads(token_sign)
    except BadData:
        return None
    else:
        return data.get('token')
