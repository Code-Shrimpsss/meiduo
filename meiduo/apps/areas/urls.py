from django.urls import path

from apps.areas.views import AreaView, SubAreaView, AddressView, UpdateAddressView, DefaultAddressView, UpdateTitleView

urlpatterns = [
    # 显示省
    path('areas/', AreaView.as_view()),
    # 显示市区
    path('areas/<area_id>/', SubAreaView.as_view()),
    # 增加地址
    path('addresses/create/', AddressView.as_view()),
    # 展示地址
    path('addresses/', AddressView.as_view()),
    # 修改和删除地址
    path('addresses/<address_id>/', UpdateAddressView.as_view()),
    # 默认地址接口
    path('addresses/<address_id>/default/',DefaultAddressView.as_view()),
    # 修改地址标题
    path('addresses/<address_id>/title/',UpdateTitleView.as_view())
]
