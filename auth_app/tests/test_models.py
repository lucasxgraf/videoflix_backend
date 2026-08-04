from django.test import TestCase
from auth_app.models import CustomUser

class CustomUserModelTest(TestCase):

    def test_create_user_sets_email(self):
        user = CustomUser.objects.create_user(
            email="user@example.com",
            password="securepassword",
        )

        self.assertEqual(user.email, "user@example.com")

    def test_create_user_is_inactive_by_default(self):
        user = CustomUser.objects.create_user(
            email="user@example.com",
            password="securepassword",
        )

        self.assertFalse(user.is_active)

    def test_create_user_password_is_hashed(self):
        user = CustomUser.objects.create_user(
            email="user@example.com",
            password="securepassword",
        )
        
        self.assertTrue(user.check_password("securepassword"))
        self.assertTrue(user.has_usable_password())