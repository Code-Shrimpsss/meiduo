from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet

from apps.goods.models import SKU, GoodsCategory, SPU, SPUSpecification
from apps.meiduo_admin.serializers.sku_serializer import SKUdeSerializer, SKUCategorieSerializer, \
    GoodsSimpleSerializer, SpecModelSerializer
from apps.meiduo_admin.utils import PageNum


# 获取所有SKU数据
class SKUModelViewSet(ModelViewSet):
    queryset = SKU.objects.all()
    serializer_class = SKUdeSerializer
    pagination_class = PageNum


# 获取所有三级类别数据
class SKUCategoriesView(ListAPIView):
    serializer_class = SKUCategorieSerializer
    # 三级路由没有下级 固为 None
    queryset = GoodsCategory.objects.filter(subs=None)


# 获取简单的SPU数据
class GoodsSimpleView(ListAPIView):
    serializer_class = GoodsSimpleSerializer
    queryset = SPU.objects.all()


# 获取商品规格
class GoodsSpecView(ListAPIView):
    serializer_class = SpecModelSerializer

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        return SPUSpecification.objects.filter(spu_id=pk)
