from django.contrib.auth.models import Group
from rest_framework.serializers import ModelSerializer


# 获取用户组数据
class GroupSerializer(ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

