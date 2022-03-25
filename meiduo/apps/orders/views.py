import json
from decimal import Decimal

from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views import View
from django_redis import get_redis_connection
from redis import Redis
from apps.areas.models import Address
from apps.goods.models import SKU
from apps.orders.models import OrderInfo, OrderGoods
from utils.views import LoginRequiredJSONMixin


# 订单结算页面显示
class OrderSettlementView(LoginRequiredJSONMixin, View):
    def get(self, request):
        user = request.user
        # 1.从redis查询所有的购物车数据  过滤出已经选中的
        # 从redis里取出skuid
        redis_conn: Redis = get_redis_connection('carts')
        # 获取hash的数据
        redis_carts = redis_conn.hgetall('carts_%s' % user.id)
        print('redis_carts', redis_carts)
        # 获取set里的数据
        carts_selected = redis_conn.smembers('selected_%s' % user.id)
        # 把选中的sku的数据 重新 放到一个新的字典里  值是他的数量
        cart_data = {}
        for sku_id in carts_selected:
            cart_data[int(sku_id)] = int(redis_carts[sku_id])
        skus = SKU.objects.filter(id__in=cart_data.keys())
        sku_list = []
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price,
                'count': cart_data[sku.id],
            })
        # 2. 运费  这里固定为10元
        freight = Decimal('10.00')
        # 3. 获取所有的用户的地址信息
        addrs = Address.objects.filter(user=user, is_deleted=False)
        addrs_list = []
        for addr in addrs:
            addrs_list.append({
                'province': addr.province.name,
                'city': addr.city.name,
                'district': addr.district.name,
                'place': addr.place,
                'province': addr.mobile,
                'id': addr.id
            })
        # 4. 拼接json返回
        context = {
            'skus': sku_list,
            'freight': freight,
            'addresses': addrs_list,
            'default_address_id': request.user.default_address,
        }
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'context': context})


# 提交订单
class OrderCommitView(LoginRequiredJSONMixin, View):
    def post(self, request):
        # 1.接收参数  地址id和支付方式
        data_dict = json.loads(request.body)
        address_id = data_dict.get('address_id')
        pay_method = data_dict.get('pay_method')
        # 2.校验
        # 校验参数
        if not all([address_id, pay_method]):
            return HttpResponseBadRequest('缺少必传参数')
        # 判断address_id是否合法
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            print(e)
            return HttpResponseBadRequest('参数address_id错误')
        # 判断pay_method是否合法
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return HttpResponseBadRequest('参数pay_method错误')
        user = request.user
        # 3.生成订单编号：年月日时分秒 + 用户编号
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)
        # 开启一个事务
        with transaction.atomic():
            # 创建事务保存点
            save_id = transaction.savepoint()
            # 回滚
            try:
                # 4.保存订单对象 OrderInfo
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    # 商品数量
                    total_count=0,
                    # 商品总金额
                    total_amount=0,
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                        'CASH'] else
                    OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )
                # 5.从redis里获取购物车商品信息   过滤被勾选的数据
                redis_conn: Redis = get_redis_connection('carts')
                # 获取hash的数据
                redis_carts = redis_conn.hgetall('carts_%s' % user.id)
                # 获取set里的数据
                carts_selected = redis_conn.smembers('selected_%s' % user.id)
                # 把选中的sku的数据 重新 放到一个新的字典里  值是他的数量
                cart_data = {}
                for sku_id in carts_selected:
                    cart_data[int(sku_id)] = int(redis_carts[sku_id])
                # 6.遍历所有的商品id
                sku_ids = cart_data.keys()
                for sku_id in sku_ids:
                    while True:
                        # 查询每一个商品的SKU数据
                        sku = SKU.objects.get(id=sku_id)
                        # 获取当前这件商品的购买数量
                        # sku_count = cart_data[sku.id]
                        # 读取原始库存
                        origin_stock = sku.stock
                        origin_sales = sku.sales
                        # 判断SKU库存
                        sku_count = cart_data[sku.id]
                        # 判断数量和库存
                        if sku_count > origin_stock:
                            # 事务回滚
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'code': 400, 'errmsg': '库存不足'})
                        # 商品的销量累加
                        # sku.sales += sku_count
                        # 商品的库存减少
                        # sku.stock -= sku_count
                        # sku.save()
                        # 乐观锁更新库存和销量
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                          sales=new_sales)
                        # 如果下单失败，但是库存足够时，继续下单，直到下单成功或者库存不足为止
                        if result == 0:
                            continue
                        # 7.生成订单商品对象  OrderGoods
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                        )
                        # 8.把sku的数量和价格累加到订单对象里面
                        order.total_count += sku_count
                        order.total_amount += (sku_count * sku.price)
                        # 下单成功或者失败就跳出循环
                        break
                # 9.总价格添加运费  然后save
                order.total_amount += order.freight
                order.save()
            except Exception as e:
                print(e)
                transaction.savepoint_rollback(save_id)
                return JsonResponse({'code': 400, 'errmsg': '下单失败'})
            # 提交订单成功，显式的提交一次事务
            transaction.savepoint_commit(save_id)
        # 10.清空购物车的所有数据  注意只删除选中的数据
        pl = redis_conn.pipeline()
        pl.hdel('carts_%s' % user.id, *carts_selected)
        pl.srem('selected_%s' % user.id, *carts_selected)
        pl.execute()
        # 11.返回json
        # 响应提交订单结果
        return JsonResponse({'code': 0, 'errmsg': '下单成功', 'order_id': order.order_id})
