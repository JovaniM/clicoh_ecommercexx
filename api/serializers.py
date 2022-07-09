from api.models import (
    Order, OrderDetail, Product
)
from rest_framework import serializers


class ProductSerializer(serializers.ModelSerializer):
    price = serializers.FloatField(required=True)

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


#####################################################
class ProductRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        return ProductSerializer(value).data

    def to_internal_value(self, data):
        obj = Product.objects.get(id=data)
        if not obj:
            raise serializers.ValidationError('Object does not exist.')
        return obj


class OrderDetailSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(required=True)
    product = ProductRelatedField(
        queryset=Product.objects.all(), read_only=False
    )

    class Meta:
        depth = 1
        exclude = ['order']
        model = OrderDetail
        read_only_fields = ['created_at', 'updated_at']


class OrderSerializer(serializers.ModelSerializer):
    details = OrderDetailSerializer(source="orderdetail_set", many=True)
    total = serializers.FloatField()
    usd_total = serializers.FloatField()

    def create(self, validated_data):
        details = validated_data.pop('orderdetail_set')
        order = Order.objects.create(**validated_data)
        for detail in details:
            #product = detail.pop('product')
            self._create_order_detail(order, detail)
            # OrderDetail.objects.create(order=order, product=product, **detail)
        return order

    #def update(self, instance, validated_data):
    #    details = None
    #    if 'orderdetail_set' in validated_data:
    #        details = validated_data.pop('orderdetail_set')
        
        # This updated Order related fields.
    #    for key in validated_data:
    #        setattr(instance, key, validated_data[key])

        # Here we manage OrderDetails
    #    previous_order_details = instance.orderdetail_set.all()
    #    updated_order_details = []
    #    for detail in details:
    #        updated_order_details.append(
    #            self._manage_order_details(
    #                instance, previous_order_details, detail
    #            )
    #        )

    #    instance.save()
    #    return instance

    def _create_order_detail(self, instance, data):
        product = data.pop('product')
        return OrderDetail.objects.create(
            order=instance, product=product, **data
        )

    #def _update_order_detail(self, instance, data):
    #    for field in instance:
    #        setattr(instance, field, data[field])

    #    instance.save()
    #    return instance

    #def _manage_order_details(self, instance, current_details, detail):
    #    if 'id' in detail:
    #        order_detail = OrderDetail.objects.get(id=detail['id'])
    #        if order_detail and order_detail in current_details:
    #            return self._update_order_detail(
    #                current_details[order_detail], detail
    #            )

    #        return None

    #    return self._create_order_detail(instance, detail)

    class Meta:
        depth = 1
        fields = '__all__'
        model = Order
        read_only_fields = [
            'created_at', 'updated_at', 'total', 'usd_total'
        ]
