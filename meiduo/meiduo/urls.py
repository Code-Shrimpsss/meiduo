from django.contrib import admin
from django.urls import path, include
from utils.converters import UsernameConverter
# 在工程的总路由出添加
from utils.converters import UUIDConverter
from django.urls import register_converter

register_converter(UUIDConverter, 'uuid')
register_converter(UsernameConverter, 'uname')

urlpatterns = [
    #
    path('admin/', admin.site.urls),
    path('', include('apps.user.urls')),
    path('', include('apps.verifications.urls')),
    path('', include('apps.oauth.urls')),
    path('', include('apps.areas.urls')),
    path('', include('apps.ad.urls')),
    path('', include('apps.goods.urls')),
    path('', include('apps.cart.urls')),
    path('', include('apps.orders.urls')),
    path('', include('apps.payment.urls')),
    path('meiduo_admin/', include('apps.meiduo_admin.urls')),
]
