from django.urls import path, include
from rest_framework import routers
from rest_framework_nested import routers as nested_routers
from api.views import (
    OrderViewSet, OrderDetailViewSet, ProductViewSet
)

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)

order_details_router = nested_routers.NestedSimpleRouter(
    router, r'orders', lookup='order'
)
order_details_router.register(
    r'order-details', OrderDetailViewSet, basename='order-detail'
)

urlpatterns = [
    path('', include(router.urls)),
    path('', include(order_details_router.urls))
]
