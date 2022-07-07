from audioop import reverse
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
import json


# Create your tests here.
class UserManagementTests(TestCase):

    def setUp(self):
        self.user_model = get_user_model()

    def test_new_user_added(self):
        total_users = self.user_model.objects.count()
        response = self.client.post(
            reverse('user-management:signup'),
            data={
                "email": "test@email.com",
                "password": "Password1234."
            }
        )
        updated_users = self.user_model.objects.count()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(total_users + 1, updated_users)

    def test_new_user_missing_email(self):
        response = self.client.post(
            reverse('user-management:signup'),
            data={
                "password": "Password1234."
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('email' in data)
        self.assertEqual(data["email"], ["This field is required."])

    def test_new_user_missing_password(self):
        response = self.client.post(
            reverse('user-management:signup'),
            data={
                "email": "test@email.com"
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('password' in data)
        self.assertEqual(data["password"], ["This field is required."])

    def test_new_user_privilegies(self):
        response = self.client.post(
            reverse('user-management:signup'),
            data={
                "email": "test@email.com",
                "password": "Password1234."
            }
        )
        updated_users = self.user_model.objects.filter(
            email="test@email.com").first()

        self.assertFalse(updated_users.staff)
        self.assertFalse(updated_users.admin)
        self.assertTrue(updated_users.is_active)
