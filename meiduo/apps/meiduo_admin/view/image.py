from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.goods.models import SKUImage, SKU
from apps.meiduo_admin.serializers.image_serializer import ImageSerializer, SKUSerializer
from apps.meiduo_admin.utils import PageNum


class ImageView(ModelViewSet):
    # 1. 指定查询集
    queryset = SKUImage.objects.filter(is_delete=0)
    # 2. 指定序列化器
    serializer_class = ImageSerializer
    # 3. 分页类
    pagination_class = PageNum

    # 重写destroy类的删除业务逻辑
    # ---- 逻辑删除
    def destroy(self, request, *args, **kwargs):
        # 1. 接收参数
        pk = kwargs.get('pk')
        sku_image = SKUImage.objects.all()
        # 2. 更改逻辑删除
        sku_image.is_delete = 1
        # 3. 保存
        sku_image.save()
        # 4. 返回响应
        return Response(status=status.HTTP_201_CREATED)

    # # ---- 真实删除
    # def destroy(self, request, *args, **kwargs):
    #     # 1. 接收参数
    #     # 1.1 获取要删除的对象ID
    #     pk = kwargs.get('pk')
    #     # 1.2 获取要删除的对象
    #     img = SKUImage.objects.get(id=pk)
    #     # 1.3 获取要删除的对象url
    #     imglongurl = img.image.url
    #     # 1.4 获取要截取后的url
    #     imgurl = imglongurl[28:]
    #
    #     # 2. 把图片上传到 fastdfs 中
    #     from fdfs_client.client import Fdfs_client
    #     # 2.1 获取图片地址
    #     client = Fdfs_client('utils/fastdfs/client.conf')
    #     # 2.2 真实删除图片
    #     client.delete_file(imgurl)
    #     # 2.3 真实删除数据
    #     img.delete()
    #
    #     # 3. 返回数据
    #     return Response(status=status.HTTP_201_CREATED)


# 用于返回 所有SKU
class SKUView(APIView):
    def get(self, request):
        data = SKU.objects.all()
        ser = SKUSerializer(data, many=True)
        return Response(ser.data)
