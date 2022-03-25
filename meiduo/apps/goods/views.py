import json

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from haystack.views import SearchView
from datetime import date
from apps.goods.models import GoodsVisitCount
from apps.ad.models import ContentCategory
from apps.goods.models import GoodsCategory, SKU
from utils.goodsuitls import get_categories, get_breadcrumb, get_goods_specs


class IndexView(View):
    def get(self, request):
        try:
            categories = get_categories()
        except Exception as e:
            print(e)
            return {'code': 1, 'errmsg': 'get data error'}

        # 获取广告数据
        contents = {}

        # - 1 ContentCategory获取所有广告的类别
        content_categories = ContentCategory.objects.all()
        # - 2 遍历所有的类别 获取每个类别下的广告
        for content_cat in content_categories:
            content_items = content_cat.content_set.filter(status=True).order_by('sequence')
            #   - 获取的时候 按照status 过滤
            #   - 按照sequence排序
            content_items_list = []
            for item_c in content_items:
                content_items_list.append(item_c.to_dict())

            contents[content_cat.key] = content_items_list

        return JsonResponse({'code': 0, 'errmsg': 'ok', "categories": categories, 'contents': contents})


# 商品列表页
class ListView(View):
    def get(self, request, category_id):
        # - 1 接收参数  校验
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering')
        # - 2 获取分类商品的数据
        # 获取列表对象
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            print(e)
            return JsonResponse({"code": 400, 'errmsg': 'ON'})
        skus = SKU.objects.filter(category=category, is_launched=True).order_by(ordering)
        #   - 2.1 分页  排序
        # 参数2 表示分页的数量
        paginator = Paginator(skus, page_size)
        page_skus = paginator.page(page)
        # 总共有几页
        count = paginator.num_pages
        #   - 2.2面包屑导航
        breadcrumb = get_breadcrumb(category)
        sku_list = []
        for sku in page_skus:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url
            })
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'count': count, 'list': sku_list, 'breadcrumb': breadcrumb})


# 商品热销排行
class HotGoodsView(View):
    def get(self, request, category_id):
        # 提供商品热销排行JSON数据
        # 根据销量倒序
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]
        # 序列化
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'hot_skus': hot_skus})


# 重写SearchView类
class MySearchView(SearchView):
    def create_response(self):
        # 获取搜索结果
        context = self.get_context()
        data_list = []
        for sku in context['page'].object_list:
            data_list.append({
                'id': sku.object.id,
                'name': sku.object.name,
                'price': sku.object.price,
                'default_image_url': sku.object.default_image.url,
                'searchkey': context.get('query'),
                'page_size': context['page'].paginator.num_pages,
                'count': context['page'].paginator.count
            })
        # 拼接参数, 返回
        return JsonResponse(data_list, safe=False)


# 商品详情页
class DetailView(View):
    def get(self, request, sku_id):
        try:
            # 获取当前sku的信息
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': 'NO'})
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
            'specs': goods_specs
        }
        return render(request, 'detail.html', context)


# 详情页分类商品访问量
class DetailVisitView(View):
    def post(self, request, category_id):
        try:
            # 1.获取当前商品
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        # 2.查询日期数据
        today_date = date.today()
        try:
            # 3.如果有当天商品分类的数据就累加数量
            count_data = category.goodschannel_set.get(date=today_date)
        except:
            # 4.没有就新建之后增加
            count_data = GoodsVisitCount()
        try:
            count_data.count += 1
            count_data.category = category
            count_data.save()
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '新增失败'})
        return JsonResponse({"code": 0, 'errmsg': 'OK'})


# 保存和查询用户浏览记录
class UserBrowseHistory(View):
    # 保存用户浏览记录
    def post(self, request):
        # 1.接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        # 2.校验参数
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({"code": 400, 'errmsg': 'sku不存在'})
        # 保存用户浏览数据
        redis_conn = get_redis_connection('history')
        # 开启管道
        pl = redis_conn.pipeline()
        user_id = request.user.id
        # 先去重
        pl.lrem('history_%s' % user_id, 0, sku_id)
        # 再储存
        pl.lpush('history_%s' % user_id, sku_id)
        # 最后截取
        pl.ltrim('history_%s' % user_id, 0, 4)
        # 执行管道
        pl.execute()
        # 响应结果
        return JsonResponse({"code": 0, "errmsg": "OK"})

    # 获取用户浏览记录
    def get(self, request):
        # 获取Redis储存的sku_id列表信息
        redis_conn = get_redis_connection('history')
        sku_ids = redis_conn.lrange('history_%s' % request.user.id, 0, -1)
        # 根据sku_ids列表数据，查询出商品sku信息
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })
        return JsonResponse({"code": 0, 'errmsg': 'OK', 'skus': skus})
