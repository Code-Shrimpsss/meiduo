from rest_framework import serializers
from apps.goods.models import SKUImage, SKU


# 获取所有图片的序列号器
class ImageSerializer(serializers.ModelSerializer):
    # 返回图片关联的sku的id值
    sku = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = SKUImage
        fields = ('sku', 'image', 'id', 'is_delete')


# 获取所有SKU的序列号器
class SKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ('id', 'name')
