from api.models import (
    Order, OrderDetail, Product
)
from api.permissions import (
    IsAuthenticatedAdminUser, IsAuthenticatedStaffUser,
    IsAuthenticatedSuperUser
)
from api.serializers import (
    OrderSerializer, OrderDetailSerializer, ProductReadOnlySerializer,
    ProductSerializer
)
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.permissions import AllowAny, IsAuthenticated


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductReadOnlySerializer
    permission_classes = [AllowAny]  # [IsAuthenticated]

    #  def get_permissions(self):
    #    if self.action not in ['list', 'retrieve']:
    #        return (
    #            IsAuthenticatedAdminUser(), IsAuthenticatedStaffUser(),
    #            IsAuthenticatedSuperUser(),
    #        )
    #    return (IsAuthenticated(), )

    def get_serializer_class(self):
        if self.action not in ['list', 'retrieve']:
            return ProductSerializer
        return ProductReadOnlySerializer


class OrderViewSet(
    viewsets.GenericViewSet, mixins.CreateModelMixin,
    mixins.DestroyModelMixin, mixins.ListModelMixin,
    mixins.RetrieveModelMixin
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]


class OrderDetailViewSet(viewsets.ModelViewSet):
    #  queryset = OrderDetail.objects.all()
    serializer_class = OrderDetailSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        order_id = self.kwargs['order_pk']
        return OrderDetail.objects.filter(order=order_id)
