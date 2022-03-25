from rest_framework.serializers import ModelSerializer
from apps.user.models import User


class UserModelSerializer(ModelSerializer):
    class Meta:
        model = User
        # 添加字段传递
        fields = ('id', 'username', 'mobile', 'email', 'password')

        # < 重写 Create 方法 >
        def create(self, validated_data):
            # 对于用户数据进行保存与密码加密
            user = User.objects.create(**validated_data)
            return user
