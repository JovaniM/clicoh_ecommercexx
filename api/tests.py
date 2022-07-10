import json

from coreapi import Object
from api import enums
from api.models import Order, OrderDetail, Product
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from mock import patch
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


class APITests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.client = APIClient()

        # Users
        self.normal_user = self.user_model.objects.create_user(
            email="test@email.com", password="Password1"
        )
        self.admin_user = self.user_model.objects.create_superuser(
            email="admin@email.com", password="Password1"
        )

        # Products
        self.product1 = Product.objects.create(
            price=100, name="Default product1", available=True
        )
        self.product2 = Product.objects.create(
            price=80, name="Default product2", available=True
        )
        self.product3 = Product.objects.create(
            price=50, name="Default product2", available=False
        )
        self.available_products = Product.objects.filter(
            available=True
        ).count()
        self.unavailable_products = Product.objects.filter(
            available=False
        ).count()

        # Orders
        self.order1 = Order.objects.create()
        self.orders_count = Order.objects.count()

        # Order Details
        self.order_detail1 = OrderDetail.objects.create(
            order=self.order1, product=self.product1, quantity=1
        )
        self.order_details_count = OrderDetail.objects.count()

    def get_token_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZATION": f'Bearer {refresh.access_token}'}

    def test_product_creation_admin_user(self):
        old_products_count = Product.objects.count()
        data = {
            "price": 20,
            "available": True,
            "name": "Product 1"
        }
        url = reverse("api:product-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        current_products_count = Product.objects.count()
        self.assertEqual(old_products_count + 1, current_products_count)

    def test_product_creation_nomal_user(self):
        data = {
            "price": 20,
            "available": True,
            "name": "Product 1"
        }
        url = reverse("api:product-list")
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_creation_no_user(self):
        data = {
            "price": 20,
            "available": True,
            "name": "Product 1"
        }
        url = reverse("api:product-list")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_product_creation_stock_ignored(self):
        name = "Product 1"
        data = {
            "price": 20,
            "available": True,
            "name": name,
            "stock": 200
        }
        url = reverse("api:product-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.post(url, data)
        product = Product.objects.get(name=name)
        self.assertEqual(product.stock, 0)

    def test_product_creation_available_default(self):
        name = "Product 1"
        data = {
            "price": 20,
            "name": name,
            "stock": 200
        }
        url = reverse("api:product-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.post(url, data)
        product = Product.objects.get(name=name)
        self.assertFalse(product.available)

    def test_product_creation_available_true(self):
        name = "Product 1"
        data = {
            "price": 20,
            "available": True,
            "name": name,
            "stock": 200
        }
        url = reverse("api:product-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.post(url, data)
        product = Product.objects.get(name=name)
        self.assertTrue(product.available)

    def test_product_required_values(self):
        data = {}
        url = reverse("api:product-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.post(url, data)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', data)
        self.assertEqual(data['price'], ["This field is required."])
        self.assertIn('name', data)
        self.assertEqual(data['name'], ["This field is required."])

    def test_product_validators(self):
        name = "Product 1"
        data = {
            "price": -1,
            "name": "Product 1"
        }
        url = reverse("api:product-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.post(url, data)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', data)
        self.assertEqual(
            data['price'], [enums.Errors.GREATER_EQUAL_ZERO_ERROR.value])

    def test_product_list_no_user(self):
        url = reverse("api:product-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_product_list_normal_user(self):
        url = reverse("api:product-list")
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_list_admin_user(self):
        url = reverse("api:product-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_list_unavailable(self):
        url = reverse("api:product-list")
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        response = self.client.get(url, {'available': False})
        data = json.loads(response.content)
        self.assertEqual(len(data), self.unavailable_products)

    def test_product_list_available(self):
        url = reverse("api:product-list")
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        response = self.client.get(url, {'available': True})
        data = json.loads(response.content)
        self.assertEqual(len(data), self.available_products)

    def test_product_list(self):
        url = reverse("api:product-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(
            len(data),
            self.unavailable_products + self.available_products
        )

    def test_product_retrieve_admin_user(self):
        url = reverse("api:product-detail", args=[self.product1.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_retrieve_normal_user(self):
        url = reverse("api:product-detail", args=[self.product1.id])
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_retrieve_no_user(self):
        url = reverse("api:product-detail", args=[self.product1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_product_put_admin_user(self):
        url = reverse("api:product-detail", args=[self.product1.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "price": 20,
            "name": "Product 1"
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_put_normal_user(self):
        url = reverse("api:product-detail", args=[self.product1.id])
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        data = {
            "price": 20,
            "name": "Product 1"
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_put_no_user(self):
        url = reverse("api:product-detail", args=[self.product1.id])
        data = {
            "price": 20,
            "name": "Product 1"
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_product_put(self):
        url = reverse("api:product-detail", args=[self.product1.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "price": 80,
            "name": "Product n"
        }
        response = self.client.put(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['price'], 80.0)
        self.assertEqual(data['name'], "Product n")

    def test_product_patch_admin_user(self):
        url = reverse("api:product-detail", args=[self.product1.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "price": 20,
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_patch_normal_user(self):
        url = reverse("api:product-detail", args=[self.product1.id])
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        data = {
            "price": 20,
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_patch_no_user(self):
        url = reverse("api:product-detail", args=[self.product1.id])
        data = {
            "price": 20,
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_product_patch(self):
        url = reverse("api:product-detail", args=[self.product1.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "price": 80,
        }
        response = self.client.patch(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['price'], 80.0)
        self.assertEqual(data['name'], self.product1.name)

    def test_product_delete_admin_user(self):
        product = Product.objects.create(price=1, name="Product")
        old_products_count = Product.objects.count()
        url = reverse("api:product-detail", args=[product.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.delete(url)
        new_products_count = Product.objects.count()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(new_products_count + 1, old_products_count)

    def test_product_delete_normal_user(self):
        url = reverse("api:product-detail", args=[self.product1.id])
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_delete_no_user(self):
        url = reverse("api:product-detail", args=[self.product1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_list_normal_user(self, _):
        url = reverse("api:order-list")
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_list_admin_user(self, _):
        url = reverse("api:order-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_order_list_no_user(self):
        url = reverse("api:order-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_create_normal_user(self, _):
        url = reverse("api:order-list")
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        data = json.dumps({
            "details": [
                {
                    "quantity": 1,
                    "product": self.product1.id
                }
            ]
        })
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_create_admin_user(self, _):
        url = reverse("api:order-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = json.dumps({
            "details": [
                {
                    "quantity": 1,
                    "product": self.product1.id
                }
            ]
        })
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_order_create_no_user(self):
        url = reverse("api:order-list")
        data = json.dumps({
            "details": [
                {
                    "quantity": 1,
                    "product": self.product1.id
                }
            ]
        })
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_order_create_required_fields(self):
        url = reverse("api:order-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {}
        response = self.client.post(url, data)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', data)
        self.assertEqual(data['details'], ['This field is required.'])

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_create_defaults(self, _):
        url = reverse("api:order-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = json.dumps({
            "details": [],
            "status": Order.OrderStatus.PROCESSED.value,
            "total": 5,
            "usd_total": 20
        })
        response = self.client.post(url, data, content_type='application/json')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            data['movement_type'],
            Order.MovementStatus.EGRESS.value
        )
        self.assertEqual(data['status'], Order.OrderStatus.DRAFT.value)
        self.assertEqual(data['total'], 0)
        self.assertEqual(data['usd_total'], 0)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_create_read_only_fields(self, _):
        url = reverse("api:order-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = json.dumps({
            "details": [],
            "status": Order.OrderStatus.PROCESSED.value,
            "total": 5,
            "usd_total": 20
        })
        response = self.client.post(url, data, content_type='application/json')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            data['movement_type'],
            Order.MovementStatus.EGRESS.value
        )
        self.assertEqual(data['status'], Order.OrderStatus.DRAFT.value)
        self.assertEqual(data['total'], 0)
        self.assertEqual(data['usd_total'], 0)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_create_writable_only_fields(self, _):
        url = reverse("api:order-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = json.dumps({
            "details": [{
                "quantity": 1,
                "product": self.product1.id
            }],
            "movement_type": Order.MovementStatus.INGRESS.value,
        })
        response = self.client.post(url, data, content_type='application/json')
        data = json.loads(response.content)

        current_order_count = Order.objects.count()
        current_order_detail_count = OrderDetail.objects.count()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            data['movement_type'],
            Order.MovementStatus.INGRESS.value
        )
        self.assertTrue(isinstance(data['details'], list))
        self.assertEqual(len(data['details']), 1)
        self.assertEqual(data['details'][0]['quantity'], 1)
        self.assertEqual(data['details'][0]['product']['id'], self.product1.id)
        self.assertEqual(current_order_count, self.orders_count + 1)
        self.assertEqual(
            current_order_detail_count,
            self.order_details_count + 1
        )

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_create_children_fields(self, _):
        url = reverse("api:order-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = json.dumps({
            "details": [{
                "id": 1,
                "quantity": 1,
                "product": self.product1.id,
                "order": 1
            }],
            "movement_type": Order.MovementStatus.INGRESS.value,
        })
        response = self.client.post(url, data, content_type='application/json')
        data = json.loads(response.content)

        current_order_count = Order.objects.count()
        current_order_detail_count = OrderDetail.objects.count()

        self.assertNotEqual(data['details'][0]['product']['id'], 1)
        self.assertEqual(current_order_count, self.orders_count + 1)
        self.assertEqual(
            current_order_detail_count,
            self.order_details_count + 1
        )

    @patch('api.models.Order._get_usd_exchange_rate', return_value=2)
    def test_order_total_field(self, _):
        url = reverse("api:order-list")
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = json.dumps({
            "details": [{
                "quantity": 5,
                "product": self.product1.id,
            }],
        })
        response = self.client.post(url, data, content_type='application/json')
        data = json.loads(response.content)

        self.assertEqual(data['total'], 5 * self.product1.price)
        self.assertEqual(data['usd_total'], (5 * self.product1.price) / 2)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_retrieve_normal_user(self, _):
        url = reverse("api:order-detail", args=[self.order1.id])
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_retrieve_admin_user(self, _):
        url = reverse("api:order-detail", args=[self.order1.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_order_retrieve_no_user(self):
        url = reverse("api:order-detail", args=[self.order1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_destroy_normal_user(self, _):
        order = Order.objects.create()
        old_order_count = Order.objects.count()
        url = reverse("api:order-detail", args=[order.id])
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        response = self.client.delete(url)
        new_order_count = Order.objects.count()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(new_order_count + 1, old_order_count)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_destroy_admin_user(self, _):
        order = Order.objects.create()
        old_order_count = Order.objects.count()
        url = reverse("api:order-detail", args=[order.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.delete(url)
        new_order_count = Order.objects.count()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(new_order_count + 1, old_order_count)

    def test_order_destroy_no_user(self):
        order = Order.objects.create()
        url = reverse("api:order-detail", args=[order.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_list_admin_user(self, _):
        url = reverse("api:order-detail-list", args=[self.order1.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_list_normal_user(self, _):
        url = reverse("api:order-detail-list", args=[self.order1.id])
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_order_detail_list_no_user(self):
        url = reverse("api:order-detail-list", args=[self.order1.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_list(self, _):
        url = reverse("api:order-detail-list", args=[self.order1.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.order_detail1.id)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_create_admin_user(self, _):
        url = reverse("api:order-detail-list", args=[self.order1.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "quantity": 1,
            "product": self.product2.id
        }
        response = self.client.post(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_create_normal_user(self, _):
        url = reverse("api:order-detail-list", args=[self.order1.id])
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        data = {
            "quantity": 1,
            "product": self.product2.id
        }
        response = self.client.post(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_order_detail_create_no_user(self):
        url = reverse("api:order-detail-list", args=[self.order1.id])
        data = {
            "quantity": 1,
            "product": self.product2.id
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_create(self, _):
        old_related_order_details_count = OrderDetail.objects.filter(
            order=self.order1
        ).count()
        url = reverse("api:order-detail-list", args=[self.order1.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "quantity": 1,
            "product": self.product2.id
        }
        response = self.client.post(url, data)
        data = json.loads(response.content)

        current_order_details_count = OrderDetail.objects.count()
        current_related_order_details_count = OrderDetail.objects.filter(
            order=self.order1
        ).count()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            current_order_details_count - 1,
            self.order_details_count
        )
        self.assertEqual(
            old_related_order_details_count + 1,
            current_related_order_details_count
        )

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_create_duplicated_product(self, _):
        url = reverse("api:order-detail-list", args=[self.order1.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "quantity": 1,
            "product": self.product1.id
        }
        response = self.client.post(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ok', data)
        # TODO: change to boolean
        self.assertEqual(data['ok'], 'False')
        self.assertIn('message', data)
        self.assertEqual(
            data['message'],
            enums.Errors.DUPLICATED_PRODUCT_ERROR.value
        )

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_create_validate_quantity(self, _):
        url = reverse("api:order-detail-list", args=[self.order1.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "quantity": 0,
            "product": self.product2.id
        }
        response = self.client.post(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('quantity', data)
        self.assertEqual(
            data['quantity'],
            [enums.Errors.GREATER_ZERO_ERROR.value]
        )

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_create_required_values(self, _):
        url = reverse("api:order-detail-list", args=[self.order1.id])
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {}
        response = self.client.post(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product', data)
        self.assertEqual(data['product'], ["This field is required."])
        self.assertIn('quantity', data)
        self.assertEqual(data['quantity'], ["This field is required."])

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_retrieve_admin_user(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_retrieve_normal_user(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_order_detail_retrieve_no_user(self):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_retrieve(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.get(url)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['id'], self.order_detail1.id)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_put_admin_user(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "quantity": 1,
            "product": self.product2.id
        }
        response = self.client.put(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_put_normal_user(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        data = {
            "quantity": 1,
            "product": self.product2.id
        }
        response = self.client.put(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_order_detail_put_no_user(self):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        data = {
            "quantity": 1,
            "product": self.product2.id
        }
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_put(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "quantity": 8,
            "product": self.product2.id
        }
        response = self.client.put(url, data)
        data = json.loads(response.content)

        updated_order = OrderDetail.objects.get(id=self.order_detail1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(updated_order.quantity, 8)
        self.assertEqual(updated_order.product, self.product2)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_put_read_only_fields(self, _):
        order = Order.objects.create()
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "order": order.id,
            "quantity": 8,
            "product": self.product2.id
        }
        response = self.client.put(url, data)
        data = json.loads(response.content)

        updated_order = OrderDetail.objects.get(id=self.order_detail1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(updated_order.order, self.order1)
        self.assertEqual(updated_order.quantity, 8)
        self.assertEqual(updated_order.product, self.product2)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_put_required_values(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {}
        response = self.client.put(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('quantity', data)
        self.assertEqual(data['quantity'], ["This field is required."])
        self.assertIn('product', data)
        self.assertEqual(data['product'], ["This field is required."])

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_put_duplicate_product(self, _):
        OrderDetail.objects.create(
            order=self.order1, product=self.product2, quantity=1
        )
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "quantity": 8,
            "product": self.product2.id
        }
        response = self.client.put(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ok', data)
        # TODO: change to boolean
        self.assertEqual(data['ok'], 'False')
        self.assertIn('message', data)
        self.assertEqual(
            data['message'],
            enums.Errors.DUPLICATED_PRODUCT_ERROR.value
        )

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_put_validate_quantity(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "quantity": 0,
            "product": self.product2.id
        }
        response = self.client.put(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('quantity', data)
        self.assertEqual(
            data['quantity'],
            [enums.Errors.GREATER_ZERO_ERROR.value]
        )

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_put_validate_editable_status(self, _):
        self.order1.status = Order.OrderStatus.CANCELLED.value
        self.order1.save()

        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "quantity": 1,
            "product": self.product2.id
        }
        response = self.client.put(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ok', data)
        # TODO: change to boolean
        self.assertEqual(data['ok'], ['False'])
        self.assertIn('message', data)
        # TODO: change to single string
        self.assertEqual(
            data['message'],
            [enums.Errors.NOT_EDITABLE_ORDER_ERROR.value]
        )

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_patch_admin_user(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "quantity": 1,
            "product": self.product2.id
        }
        response = self.client.patch(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_patch_normal_user(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)
        data = {
            "quantity": 1,
            "product": self.product2.id
        }
        response = self.client.patch(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_order_detail_patch_no_user(self):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        data = {
            "quantity": 1,
            "product": self.product2.id
        }
        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_patch(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "product": self.product2.id
        }
        response = self.client.patch(url, data)
        data = json.loads(response.content)

        updated_order = OrderDetail.objects.get(id=self.order_detail1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(updated_order.product, self.product2)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_patch_read_only_fields(self, _):
        order = Order.objects.create()
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "order": order.id,
            "quantity": 8
        }
        response = self.client.patch(url, data)
        data = json.loads(response.content)

        updated_order = OrderDetail.objects.get(id=self.order_detail1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(updated_order.order, self.order1)
        self.assertEqual(updated_order.quantity, 8)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_patch_duplicate_product(self, _):
        OrderDetail.objects.create(
            order=self.order1, product=self.product2, quantity=1
        )
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "product": self.product2.id
        }
        response = self.client.patch(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ok', data)
        # TODO: change to boolean
        self.assertEqual(data['ok'], 'False')
        self.assertIn('message', data)
        self.assertEqual(
            data['message'],
            enums.Errors.DUPLICATED_PRODUCT_ERROR.value
        )

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_patch_validate_quantity(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "quantity": 0
        }
        response = self.client.patch(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('quantity', data)
        self.assertEqual(
            data['quantity'],
            [enums.Errors.GREATER_ZERO_ERROR.value]
        )

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_patch_validate_editable_status(self, _):
        self.order1.status = Order.OrderStatus.CANCELLED.value
        self.order1.save()

        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        data = {
            "product": self.product2.id
        }
        response = self.client.patch(url, data)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ok', data)
        # TODO: change to boolean
        self.assertEqual(data['ok'], ['False'])
        self.assertIn('message', data)
        # TODO: change to single string
        self.assertEqual(
            data['message'],
            [enums.Errors.NOT_EDITABLE_ORDER_ERROR.value]
        )

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_delete_admin_user(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.delete(url)
        current_related_order_details = OrderDetail.objects.filter(
            order=self.order1
        ).count()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            self.order_details_count - 1,
            current_related_order_details
        )

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_delete_normal_user(self, _):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)

        response = self.client.delete(url)
        current_related_order_details = OrderDetail.objects.filter(
            order=self.order1
        ).count()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            self.order_details_count - 1,
            current_related_order_details
        )

    def test_order_detail_delete_no_user(self):
        url = reverse(
            "api:order-detail-detail",
            args=[self.order1.id, self.order_detail1.id]
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_process_admin_user(self, _):
        url = reverse(
            "api:order-process",
            args=[self.order1.id]
        )
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(**token)
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('api.models.Order._get_usd_exchange_rate', return_value=1)
    def test_order_detail_process_normal_user(self, _):
        url = reverse(
            "api:order-process",
            args=[self.order1.id]
        )
        token = self.get_token_for_user(self.normal_user)
        self.client.credentials(**token)

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_order_detail_process_no_user(self):
        url = reverse(
            "api:order-process",
            args=[self.order1.id]
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    # deleting a used product must be raise an exception
    # deleting a order must delete order details
    # create ingres and apply
    # create egress and apply
    # create ingres on process and cancel
    # create egress on process and cancel
    # create egres without space
    # create ingress without space
    # create apply not editable
    # create cancel not editable