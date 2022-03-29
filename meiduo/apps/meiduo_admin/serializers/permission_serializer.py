from django.contrib.auth.models import Permission
from rest_framework.serializers import ModelSerializer
from django.contrib.auth.models import ContentType


# 获取权限数据
class PermissionSerializer(ModelSerializer):
    class Meta:
        model = Permission
        fields = "__all__"


# 保存用户权限
class ContentTypeSerializer(ModelSerializer):
    class Meta:
        model = ContentType
        fields = ('id', 'name')
