from django.contrib.auth import get_user_model
from django.test import TestCase


# Create your tests here.
class CustomUserTests(TestCase):

    def setUp(self) -> None:
        self.user_model = get_user_model()

    def test_user_creation(self):
        new_user = self.user_model.objects.create_user(
            email="test-user@email.com", password="Password1234"
        )
        self.assertFalse(new_user.staff)
        self.assertFalse(new_user.admin)
        self.assertTrue(new_user.is_active)

    def test_user_no_email(self):
        with self.assertRaises(ValueError) as err:
            new_user = self.user_model.objects.create_user(
                email=None
            )

        self.assertEqual(
            err.exception.args[0], 'Users must have an email address')

    def test_user_staff(self):
        new_user = self.user_model.objects.create_staffuser(
            email="test-user@email.com", password="Password1234"
        )
        self.assertTrue(new_user.staff)
        self.assertFalse(new_user.admin)
        self.assertTrue(new_user.is_active)

    def test_user_add(self):
        new_user = self.user_model.objects.create_superuser(
            email="test-user@email.com", password="Password1234"
        )
        self.assertTrue(new_user.staff)
        self.assertTrue(new_user.admin)
        self.assertTrue(new_user.is_active)
