from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.viewsets import ModelViewSet
from apps.meiduo_admin.serializers.permission_serializer import PermissionSerializer, ContentTypeSerializer
from apps.meiduo_admin.utils import PageNum


# 获取权限数据
class PermissionView(ModelViewSet):
    queryset = Permission.objects.order_by('id')
    serializer_class = PermissionSerializer
    pagination_class = PageNum


# 保存权限数据
class ContentTypeView(APIView):
    def get(self, request):
        # 查询全选分类
        content = ContentType.objects.all()
        # 返回结果
        ser = ContentTypeSerializer(content, many=True)
        return Response(ser.data)
