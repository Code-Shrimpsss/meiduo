from django.db import transaction
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from apps.goods.models import SKU, GoodsCategory, SpecificationOption, SPUSpecification, SPU, SKUSpecification


class SKUSpecificationSerialzier(ModelSerializer):
    # SKU 规格表序列化器
    spec_id = serializers.IntegerField()
    option_id = serializers.IntegerField()

    class Meta:
        model = SKUSpecification
        fields = ("spec_id", "option_id")


# SKU的序列化器
class SKUdeSerializer(ModelSerializer):
    # 添加2个字段接收 category_id 与 spu_id
    spu_id = serializers.IntegerField()
    category_id = serializers.IntegerField()
    # 自己定义 spu 和 category 字段 为 StringRelatedField
    spu = serializers.StringRelatedField(read_only=True)
    category = serializers.StringRelatedField(read_only=True)

    # 定义specs字段来接收规格信息 : spec_id , option_id 与 SKUSpecification 对应
    # 定义 SKUSpecificationSerialzier 序列化器来实现反序列化操作
    specs = SKUSpecificationSerialzier(many=True)

    class Meta:
        model = SKU
        fields = '__all__'

    # 重写 create 方法
    def create(self, validated_data):
        # 1 获取规格数据并从字典里删除
        specs = validated_data.pop('specs')

        # ----- 创建事务(悲观锁)
        with transaction.atomic():
            # --- 获取保存点
            save_point = transaction.savepoint()
            try:
                # 2 保存sku
                sku = SKU.objects.create(**validated_data)
                # 3循环specs保存规格
                for i in specs:
                    SKUSpecification.objects.create(sku=sku, **i)
            except Exception as e:
                # --- 若报错回滚到保存点 save_point
                transaction.savepoint_rollback(save_point)
            else:
                # --- 执行成功则提交保存
                transaction.savepoint_commit(save_point)
        # 4返回sku对象
        return sku

    # 重写 update 方法
    def update(self, instance, validated_data):
        specs = validated_data.pop('specs')
        super().update(instance, validated_data)
        for spec in specs:
            new_spec_id = spec.get('spec_id')
            new_option_id = spec.get('option_id')
            SKUSpecification.objects.filter(sku=instance, spec_id=new_spec_id).update(option_id=new_option_id)
        return instance


# 三级路由的序列化器
class SKUCategorieSerializer(ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = '__all__'


# SPU表名称信息的序列化器
class GoodsSimpleSerializer(ModelSerializer):
    class Meta:
        model = SPU
        fields = '__all__'


# 供商品规格使用的序列化器
class GoodsOptionSerializer(ModelSerializer):
    class Meta:
        model = SpecificationOption
        fields = ('id', 'value')


# 获取商品规格的序列化器
class SpecModelSerializer(ModelSerializer):
    options = GoodsOptionSerializer(many=True)
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()

    class Meta:
        model = SPUSpecification
        fields = '__all__'
