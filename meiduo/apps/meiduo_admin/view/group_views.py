from django.contrib.auth.models import Group, Permission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.meiduo_admin.serializers.group_serializer import GroupSerializer
from apps.meiduo_admin.serializers.permission_serializer import PermissionSerializer
from apps.meiduo_admin.utils import PageNum


# 获取用户组数据
class GroupView(ModelViewSet):
    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    pagination_class = PageNum


# 新增用户组数据
class GroupAddView(APIView):
    def get(self, request):
        pers = Permission.objects.all()
        ser = PermissionSerializer(pers, many=True)
        return Response(ser.data)
