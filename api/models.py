from django.db import models
from api import enums
from api.utils import requests_retry_session
from api.validators import greater_equal_than_zero
from rest_framework.exceptions import ValidationError
from rest_framework import status

import json


class Product(models.Model):
    available = models.BooleanField("available", default=False)
    created_at = models.DateTimeField("created_at", auto_now_add=True)
    name = models.CharField("name", null=False, max_length=256)
    price = models.FloatField(
        "price", null=False, default=0, validators=[greater_equal_than_zero])
    stock = models.IntegerField("stock", null=False, default=0)
    updated_at = models.DateTimeField("updated_at", auto_now=True)

    def is_valid(self):
        if not self.available:
            raise ValidationError(
                enums.Errors.PRODUCT_NOT_AVAILABLE_ERROR.value
            )

    def can_be_supplied(self, quantity):
        self.is_valid()
        return self.stock >= quantity

    def add_stock_quantity(self, quantity):
        greater_equal_than_zero(quantity)
        self.stock += quantity
        self.save()

    def substract_stock_quantity(self, quantity):
        greater_equal_than_zero(quantity)
        self.stock -= quantity
        self.save()


class Order(models.Model):
    class MovementStatus(models.TextChoices):
        INGRESS = 'INGRESS', 'INGRESS'
        EGRESS = 'EGRESS', 'EGRESS'

    class OrderStatus(models.TextChoices):
        CANCELLED = 'CANCELLED', 'CANCELLED'
        DRAFT = 'DRAFT', 'DRAFT'
        PROCESSED = 'PROCESSED', 'PROCESSED'

    EDITABLE_STATUS = [OrderStatus.DRAFT]

    created_at = models.DateTimeField("created_at", auto_now_add=True)
    details = models.ManyToManyField(Product, through='OrderDetail')
    movement_type = models.CharField(
        null=False, choices=MovementStatus.choices,
        default=MovementStatus.EGRESS,
        db_index=True, max_length=10
    )
    status = models.CharField(
        choices=OrderStatus.choices, default=OrderStatus.DRAFT,
        null=False, max_length=10
    )
    updated_at = models.DateTimeField("updated_at", auto_now=True)

    @property
    def total(self):
        total = 0
        for detail in self.orderdetail_set.all():
            total += detail.quantity * detail.product.price

        return total

    @property
    def usd_total(self):
        total = self.total
        return total / self._get_usd_exchange_rate()

    def _get_usd_exchange_rate(self):
        URL = "https://www.dolarsi.com/api/api.php?type=valoresprincipales"
        response = requests_retry_session().get(
            url=URL,
            timeout=10
        )

        if response.status_code != status.HTTP_200_OK:
            raise Exception("We can't get exchange rate from service.")

        data = json.loads(response.content)
        for d in data:
            if not ('casa' in d and d['casa']):
                raise Exception("Wrong format on exchange response.")
            if not ('nombre' in d['casa'] and 'compra' in d['casa']):
                raise Exception("Wrong format on exchange response.")
            if d['casa']['nombre'] == 'Dolar Blue':
                return float(d['casa']['compra'].replace(',', '.'))
        raise Exception("Expected change not found.")


class OrderDetail(models.Model):
    created_at = models.DateTimeField("created_at", auto_now_add=True)
    order = models.ForeignKey(
        'Order', on_delete=models.CASCADE, null=False
    )
    product = models.ForeignKey(
        'Product', on_delete=models.PROTECT, null=False
    )
    quantity = models.IntegerField(
        "quantity", null=False, validators=[greater_equal_than_zero])
    updated_at = models.DateTimeField("updated_at", auto_now=True)

    class Meta:
        unique_together = [['product', 'order']]
