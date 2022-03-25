#!/usr/bin/env python


import sys

sys.path.insert(0, '../')
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo.settings")
import django

django.setup()
from django.template import loader

from apps.goods.models import SKU
from meiduo import settings
from utils.goodsuitls import get_categories, get_breadcrumb, get_goods_specs


def genarate_detail(sku_id):
    """生成详情页面保存到html"""
    # 获取当前sku的信息

    sku = SKU.objects.get(id=sku_id)

    # 查询商品频道分类
    categories = get_categories()
    # 查询面包屑导航
    breadcrumb = get_breadcrumb(sku.category)
    # 查询SKU规格信息
    goods_specs = get_goods_specs(sku)

    # 渲染页面
    context = {
        'categories': categories,
        'breadcrumb': breadcrumb,
        'sku': sku,
        'specs': goods_specs,
    }
    # 获取模板对象
    template = loader.get_template("detail.html")
    # 渲染模板
    html_text = template.render(context)
    # 渲染好的模板保存到file
    file_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'front_end_pc/goods/' + str(sku_id) + '.html')
    with open(file_path, 'w') as f:
        f.write(html_text)


if __name__ == '__main__':
    skus = SKU.objects.all()
    for sku in skus:
        print(sku.id)
        genarate_detail(sku.id)
