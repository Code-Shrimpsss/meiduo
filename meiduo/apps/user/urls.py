from django.urls import path

from apps.user.views import UsernameCountView, MobileCountView, RegisterView, LoginView, LogoutView, UserInfoView, \
    SaveEmailView, EmailVerifyView, ChangePasswordView

urlpatterns = [
    # 用户名重复
    path('usernames/<uname:username>/count/', UsernameCountView.as_view()),
    # 手机号重复
    path('mobiles/<uname:mobile>/count/', MobileCountView.as_view()),
    # 用户注册
    path('register/', RegisterView.as_view()),
    # 用户名登录
    path('login/', LoginView.as_view()),
    # 退出登录
    path('logout/', LogoutView.as_view()),
    # 用户中心
    path('info/', UserInfoView.as_view()),
    # 邮箱
    path('emails/', SaveEmailView.as_view()),
    # 邮箱激活
    path('emails/verification/', EmailVerifyView.as_view()),
    # 修改密码
    path('password/', ChangePasswordView.as_view())
]
