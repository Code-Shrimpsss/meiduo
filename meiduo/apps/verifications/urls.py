from django.urls import path

from apps.verifications.views import ImageCodeView, SmsView

urlpatterns = [
    # 图形验证码
    path('image_codes/<uuid>/', ImageCodeView.as_view()),
    # 短信验证码
    path('sms_codes/<mobile>/',SmsView.as_view())
]
