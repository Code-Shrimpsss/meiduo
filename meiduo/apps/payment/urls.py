from django.urls import path

from apps.payment.views import PaymentView, PaymentStatusView

urlpatterns = [
    path('payment/<int:order_id>/', PaymentView.as_view()),
    path('payment/status/', PaymentStatusView.as_view())
]
