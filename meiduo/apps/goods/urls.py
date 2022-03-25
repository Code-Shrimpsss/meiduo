from django.urls import path

from apps.cart.views import CartsSimpleView
from apps.goods.views import IndexView, ListView, HotGoodsView, MySearchView, DetailView, DetailVisitView, \
    UserBrowseHistory

urlpatterns = [
    path('index/', IndexView.as_view()),
    path('list/<category_id>/skus/', ListView.as_view()),
    path('hot/<category_id>/', HotGoodsView.as_view()),
    path('search/', MySearchView()),
    path('detail/<sku_id>/', DetailView.as_view()),
    path('detail/visit/<category_id>/', DetailVisitView.as_view()),
    path('browse_histories/',UserBrowseHistory.as_view()),
    path('carts/simple/',CartsSimpleView.as_view())
]
