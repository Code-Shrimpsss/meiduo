import json
import re

from django import http
from django.core.cache import cache
from django.http import JsonResponse
from django.views import View
from apps.areas.models import Area, Address
from utils.views import LoginRequiredJSONMixin


# 显示省
class AreaView(View):
    def get(self, request):
        province_list = cache.get('provinces')
        if not province_list:
            # 1.去数据库查询所有的省份数据
            try:
                areas = Area.objects.filter(parent=None)
            except Exception as e:
                print(e)
                return JsonResponse({'code': 400, 'errmsg': '获取省份失败，网络异常'})
            province_list = []
            for a in areas:
                province_list.append({'id': a.id, 'name': a.name})
            # 省区缓存数据
            cache.set('provinces', province_list, 3600 * 24 * 30)
        # 2.返回
        return JsonResponse({'code': 0, 'province_list': province_list})


# 显示市区
class SubAreaView(View):
    def get(self, request, area_id):
        # 1.获取路径中的上一级的地区id
        # 正则校验area_id
        # 2.根据上一级的id获取下一级的数据（数据库操作）
        subs = cache.get('cities_%s' % area_id)
        if not subs:
            try:
                subareas = Area.objects.filter(parent_id=area_id)
            except Exception as e:
                print(e)
                return JsonResponse({'code': 400, 'errmsg': '获取市区失败，网络异常'})
            # 3.把下一级数据 作拼接
            subs = []
            for a in subareas:
                subs.append({'id': a.id, 'name': a.name})
            # 市区缓存数据
            cache.set('cities_%s' % area_id, subs, 3600 * 24 * 30)
        # 4返回给前端
        return JsonResponse({'code': 0, 'sub_data': {'subs': subs}})


# 新增收货地址
class AddressView(LoginRequiredJSONMixin, View):
    def post(self, request):
        body = request.body
        data_dict = json.loads(body)
        # 接收参数
        receiver = data_dict.get('receiver')
        province_id = data_dict.get('province_id')
        city_id = data_dict.get('city_id')
        district_id = data_dict.get('district_id')
        place = data_dict.get('place')
        mobile = data_dict.get('mobile')
        tel = data_dict.get('tel')
        email = data_dict.get('email')
        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseBadRequest('缺少必传参数')
        # 保存地址信息
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email)
            # 设置address为默认地址
            request.user.default_address = address.id
            request.user.save()
        except Exception as e:
            print(e)
            return http.JsonResponse({'code': 400, 'errmsg': '保存失败'})
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'city': address.city.name,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email
        }
        # 返回成功信息
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'address': address_dict})

    def get(self, request):
        # 1.获取用户对象
        user = request.user
        # 2.获取所有地址
        try:
            addresses = user.addresses.all().filter(is_deleted=False)
            # 创建一个空列表 存地址的字典数据
            address_dict_list = []
            # 循环拼接字典 添加到列表里
            for address in addresses:
                address_dict = {
                    'id': address.id,
                    'title': address.title,
                    'receiver': address.receiver,
                    'city': address.city.name,
                    'district': address.district.name,
                    'place': address.place,
                    'mobile': address.mobile,
                    'tel': address.tel,
                    'email': address.email
                }
                # 3拼接列表
                address_dict_list.insert(0, address_dict)
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '查询失败'})
        # 4.返回
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'addresses': address_dict_list,
                             'default_address_id': request.user.default_address})


# 修改和删除地址
class UpdateAddressView(LoginRequiredJSONMixin, View):
    # 修改地址
    def put(self, request, address_id):
        body = request.body
        data_dict = json.loads(body)
        receiver = data_dict.get('receiver')
        province_id = data_dict.get('province_id')
        city_id = data_dict.get('city_id')
        district_id = data_dict.get('district_id')
        place = data_dict.get('place')
        mobile = data_dict.get('mobile')
        tel = data_dict.get('tel')
        email = data_dict.get('email')
        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400, 'errmsg': '参数mobile有误'})
        # 判断地址是否存在，并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '更新地址失败'})
        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        # 响应更新地址结果
        return JsonResponse({'code': 0, 'errmsg': '更新地址成功', 'address': address_dict})

    # 删除地址
    def delete(self, request, address_id):
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)
            # 将地址逻辑删除设置为True
            address.is_deleted = True
            address.save()
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '删除地址成功'})
        return JsonResponse({'code': 0, 'errmsg': '删除地址成功'})


# 设置默认地址
class DefaultAddressView(LoginRequiredJSONMixin, View):
    def put(self, request, address_id):
        try:
            # 接受地址，查询地址
            address = Address.objects.get(id=address_id)
            # 设置为默认地址
            request.user.default_address = address.id
            request.user.save()
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '设置为默认地址失败'})
        # 响应设置默认地址结果
        return JsonResponse({'code': 0, 'errmsg': '设置为默认地址'})


# 修改地址标题
class UpdateTitleView(View):
    def put(self, request, address_id):
        body = request.body
        data_dict = json.loads(body)
        title = data_dict.get('title')
        try:
            # 查询地址
            address = Address.objects.get(id=address_id)
            # 设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '设置地址标题失败'})
        return JsonResponse({'code': 0, 'errmsg': '设置地址标题成功'})
