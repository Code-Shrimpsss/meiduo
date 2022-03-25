from django.urls import path

from apps.oauth.views import WeiboAuthURLView, WeiboAuthUserView

urlpatterns = [
    # 获取登录页面的视图
    path('qq/authorization/', WeiboAuthURLView.as_view()),
    path('oauth_callback/', WeiboAuthUserView.as_view()),


]
