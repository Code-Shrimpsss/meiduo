from rest_framework.generics import ListCreateAPIView
from apps.meiduo_admin.serializers.user_serializers import UserModelSerializer
from apps.meiduo_admin.utils import PageNum
from apps.user.models import User


class UserListView(ListCreateAPIView):
    # # 1. 指定查询集
    # queryset = User.objects.all()
    # 2. 指定序列化器
    serializer_class = UserModelSerializer
    # 3. 分页类
    pagination_class = PageNum

    # 重写 get_querysey
    def get_queryset(self):
        # 1. 获取前端传递的 keyword
        keyword = self.request.query_params.get('keyword')
        # 2. 判断 (若不存在或为空 则返回全部, 否则返回查询对应的keyword)
        if not keyword:
            return User.objects.all()
        else:
            return User.objects.filter(username=keyword)
