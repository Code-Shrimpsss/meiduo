from django.contrib.auth.models import Group
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.meiduo_admin.serializers.admin_serializer import AdminSerializer
from apps.meiduo_admin.serializers.group_serializer import GroupSerializer
from apps.meiduo_admin.utils import PageNum
from apps.user.models import User


# 获取管理员用户列表数据
class AdminView(ModelViewSet):
    queryset = User.objects.filter(is_staff=True)
    serializer_class = AdminSerializer
    pagination_class = PageNum


# 获取分组表数据
class AdminSimpleAPIView(APIView):
    def get(self, request):
        pers = Group.objects.all()
        ser = GroupSerializer(pers, many=True)
        return Response(ser.data)