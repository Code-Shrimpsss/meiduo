from django.urls import path

from apps.cart.views import CartsView, CartSelectView, CartsSimpleView

urlpatterns = [
    path('carts/', CartsView.as_view()),
    path('carts/selection/', CartSelectView.as_view()),
    path('carts/simple/', CartsSimpleView.as_view())
]
