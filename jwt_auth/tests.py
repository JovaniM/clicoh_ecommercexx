from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

import json


# Create your tests here.
class JWTAuthTests(TestCase):

    def setUp(self) -> None:
        self.user_model = get_user_model()
        self.user1 = self.user_model(
            email="test@email.com", is_active=True
        )
        self.user1.set_password("Password1234.")
        self.user1.save()

    def test_obtain_token(self):
        response = self.client.post(
            reverse("jwt-auth:token_pair"),
            data={
                "email": "test@email.com",
                "password": "Password1234."
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', data)
        self.assertIn('access', data)

    def test_refresh_token_wrong_refresh(self):
        response = self.client.post(
            reverse("jwt-auth:token_refresh"),
            data={
                "refresh": "somevalue"
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("code", data)
        self.assertEqual(data["code"], "token_not_valid")
