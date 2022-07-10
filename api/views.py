from api.models import (
    Order, OrderDetail, Product
)
from api.permissions import (
    IsAuthenticatedAdminUser, IsAuthenticatedStaffUser,
    IsAuthenticatedSuperUser
)
from api.serializers import (
    OrderDetailSerializer, OrderSerializer, OrderStatusSerializer,
    ProductReadOnlySerializer, ProductSerializer
)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, OR
from rest_framework.response import Response


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductReadOnlySerializer

    def get_queryset(self):
        params = {}

        if 'available' in self.request.query_params:
            params['available'] = self.request.query_params['available']

        return Product.objects.filter(**params).order_by('id')

    def get_permissions(self):
        if self.action not in ['list', 'retrieve']:
            self.permission_classes = [
                IsAuthenticatedStaffUser | IsAuthenticatedAdminUser | IsAuthenticatedSuperUser,
            ]
        else:
            self.permission_classes = [IsAuthenticated, ]
        return super(ProductViewSet, self).get_permissions()

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
    permission_classes = [IsAuthenticated]

    def _manage_order_status(self, order, status):
        if not order:
            # TODO: add to custom response
            return Response(
                {"ok": False, "message": "error"},
                status=status.HTTP_404_NOT_FOUND
            )
        order.status = status
        order.save()
        # TODO: add to custom response
        return Response(OrderSerializer(order).data)

    @action(
        detail=True, methods=['post'], serializer_class=OrderStatusSerializer
    )
    def process(self, request, pk=None):
        order = Order.objects.get(id=pk)
        if order.status not in Order.EDITABLE_STATUS:
            # TODO: add to custom response
            return Response({
                "ok": False,
                "message": "Cant proccess with curren status value."
            }, status=status.HTTP_400_BAD_REQUEST)

        products = order.details.all()
        for product in products:
            if order.movement_type == Order.MovementStatus.EGRESS.value:
                product.can_be_supplied(product.quantity)
                product.substract_stock_quantity(product.quantity)
            else:
                product.add_stock_quantity(product.quantity)

        return self._manage_order_status(
            order, Order.OrderStatus.PROCESSED.value
        )

    @action(
        detail=True, methods=['post'], serializer_class=OrderStatusSerializer
    )
    def cancel(self, request, pk=None):
        order = Order.objects.get(id=pk)
        if order.status == Order.OrderStatus.PROCESSED.value:
            # TODO: add to custom response
            return Response({
                "ok": False,
                "message": "Already cancelled."
            }, status=status.HTTP_400_BAD_REQUEST)
        if order.status == Order.OrderStatus.PROCESSED.value:
            products = order.details
            for product in products:
                if order.movement_type == Order.MovementStatus.INGRESS.value:
                    product.add_stock_quantity(product.quantity)
                else:
                    product.can_be_supplied(product.quantity)
                    product.substract_stock_quantity(product.quantity)

        return self._manage_order_status(
            order, Order.OrderStatus.CANCELLED.value
        )


class OrderDetailViewSet(viewsets.ModelViewSet):
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super(OrderDetailViewSet, self).get_serializer_context()
        context.update({"order_pk": self.kwargs['order_pk']})
        return context

    def get_queryset(self):
        order_id = self.kwargs['order_pk']
        return OrderDetail.objects.filter(order=order_id).order_by('id')
