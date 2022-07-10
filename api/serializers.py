from django.db.utils import IntegrityError
from api import enums
from api.models import (
    Order, OrderDetail, Product
)
from api.utils import error_response
from api.validators import greater_than_zero
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class ProductSerializer(serializers.ModelSerializer):
    price = serializers.FloatField(required=True)

    def validate_price(self, value):
        greater_than_zero(value)
        return value

    class Meta:
        fields = '__all__'
        model = Product
        read_only_fields = ['created_at', 'updated_at', 'stock']


class ProductReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Product
        read_only_fields = [
            'available', 'created_at', 'name', 'price', 'stock', 'updated_at'
        ]


class ProductRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        return ProductSerializer(value).data

    def to_internal_value(self, data):
        obj = Product.objects.get(id=data)
        if not obj:
            raise serializers.ValidationError('Object does not exist.')
        return obj


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['status']
        model = Order
        read_only_fields = ['status']


class OrderDetailSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(required=True)
    product = ProductRelatedField(
        queryset=Product.objects.all(), read_only=False
    )

    def validate_quantity(self, value):
        greater_than_zero(value)
        return value

    def _get_related_order(self):
        order = Order.objects.filter(
            id=self.context.get('order_pk', None)
        ).first()
        #if not order:
        #    raise error_response(
        #        ValidationError, enums.Errors.MISSING_ORDER_ERROR.value
        #    )
        return order

    def _check_duplicated_products(self, order_products, product):
        if product and product in order_products:
            raise error_response(
                ValidationError, enums.Errors.DUPLICATED_PRODUCT_ERROR.value
            )

    def validate(self, attrs):
        order = self._get_related_order()
        #if not order:
        #    raise error_response(
        #        ValidationError, enums.Errors.MISSING_ORDER_ERROR.value
        #    )

        if order and order.status not in Order.EDITABLE_STATUS:
            raise error_response(
                ValidationError, enums.Errors.NOT_EDITABLE_ORDER_ERROR.value
            )
        return attrs

    def update(self, instance, validated_data):
        order = self._get_related_order()
        # Check duplicity on Order parent
        order_products = [x.product for x in order.orderdetail_set.all() if x != instance]
        product = validated_data.get('product', None)
        self._check_duplicated_products(order_products, product)

        for field in validated_data:
            setattr(instance, field, validated_data[field])

        instance.save()
        return instance

    def create(self, validated_data):
        order = self._get_related_order()
        # Check duplicity on Order parent
        order_products = order.details.all()
        product = validated_data.get('product', None)
        self._check_duplicated_products(order_products, product)

        validated_data['order'] = order
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise error_response(
                ValidationError, enums.Errors.INTEGRITY_PRODUCT_ERROR.value
            )

    class Meta:
        depth = 1
        exclude = ['order']
        model = OrderDetail
        read_only_fields = ['created_at', 'updated_at']


class OrderSerializer(serializers.ModelSerializer):
    details = OrderDetailSerializer(source="orderdetail_set", many=True)
    total = serializers.FloatField(required=False, read_only=True)
    usd_total = serializers.FloatField(required=False, read_only=True)

    def create(self, validated_data):
        details = validated_data.pop('orderdetail_set')
        order = Order.objects.create(**validated_data)
        for detail in details:
            self._create_order_detail(order, detail)
        return order

    def _create_order_detail(self, instance, data):
        product = data.pop('product')
        return OrderDetail.objects.create(
            order=instance, product=product, **data
        )

    class Meta:
        depth = 1
        fields = '__all__'
        model = Order
        read_only_fields = [
            'created_at', 'updated_at', 'total', 'usd_total', 'status'
        ]
