from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.routers import DefaultRouter
from .view.count_views import UserDailyActiveCountView, \
    UserDailyOrderCountView, UserDayCountView, UserMonthCountView
from .view.user_view import UserListView
from .view.image import ImageView, SKUView

urlpatterns = [
    # 用于返回 token
    path('authorizations/', obtain_jwt_token),
    # 用于返回 当日活跃人数
    path('statistical/day_active/', UserDailyActiveCountView.as_view()),
    # 用于返回 当日下单人数
    path('statistical/day_orders/', UserDailyOrderCountView.as_view()),
    # 用于返回 当日新增人数
    path('statistical/day_increment/', UserDayCountView.as_view()),
    # 用于返回 当月新增人数
    path('statistical/month_increment/', UserMonthCountView.as_view()),
    # 用于返回 用户总人数
    path('users/', UserListView.as_view()),
    # 用于返回 所有SKU
    path('skus/simple/', SKUView.as_view()),
]

# ----- 使用默认实例
router = DefaultRouter()
# ----- 注册路由
router.register(r'skus/images', ImageView, basename='imagesku')
# ----- 追加到 urlpatterns 中
urlpatterns += router.urls
