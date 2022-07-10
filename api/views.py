from api import enums
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
from api.utils import http_error_response, http_success_response
from django.db.models import ProtectedError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductReadOnlySerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return http_error_response(
                enums.Errors.PROTECTED_PRODUCT_ERROR.value,
                status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

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

    def _manage_order_status(self, order, order_status):
        if not order:
            return http_error_response(
                enums.Errors.MISSING_ORDER_ERROR.value,
                status.HTTP_404_NOT_FOUND
            )

        order.status = order_status
        order.save()
        return http_success_response(
            OrderSerializer(order).data,
            status.HTTP_200_OK
        )

    @action(
        detail=True, methods=['post'], serializer_class=OrderStatusSerializer
    )
    def process(self, request, pk=None):
        order = Order.objects.get(id=pk)
        if order.status not in Order.EDITABLE_STATUS:
            return http_error_response(
                enums.Errors.NOT_EDITABLE_ORDER_ERROR.value,
                status.HTTP_400_BAD_REQUEST
            )

        details = order.orderdetail_set.all()
        for detail in details:
            if order.movement_type == Order.MovementStatus.EGRESS.value:
                if not detail.product.can_be_supplied(detail.quantity):
                    return http_error_response(
                        enums.Errors.STOCK_AVAILABILITY_ERROR.value,
                        status.HTTP_400_BAD_REQUEST
                    )

                detail.product.substract_stock_quantity(detail.quantity)
            else:
                detail.product.add_stock_quantity(detail.quantity)

        return self._manage_order_status(
            order, Order.OrderStatus.PROCESSED.value
        )

    @action(
        detail=True, methods=['post'], serializer_class=OrderStatusSerializer
    )
    def cancel(self, request, pk=None):
        order = Order.objects.get(id=pk)
        if order.status == Order.OrderStatus.CANCELLED.value:
            return http_error_response(
                enums.Errors.ORDER_ALREADY_CANCELLED.value,
                status.HTTP_400_BAD_REQUEST
            )

        if order.status == Order.OrderStatus.PROCESSED.value:
            details = order.orderdetail_set.all()
            for detail in details:
                if order.movement_type == Order.MovementStatus.INGRESS.value:
                    if not (detail.product.can_be_supplied(detail.quantity)):
                        return Response({
                            "ok": False,
                            "message": "This order cant be cancelled due stock availability."
                        }, status=status.HTTP_400_BAD_REQUEST)

                    detail.product.substract_stock_quantity(detail.quantity)
                else:
                    detail.product.add_stock_quantity(detail.quantity)

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
