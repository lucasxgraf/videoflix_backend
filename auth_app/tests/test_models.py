from django.test import TestCase
from auth_app.models import CustomUser


class CustomUserModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="user@example.com",
            password="securepassword",
        )

    def test_create_user_sets_email(self):
        self.assertEqual(self.user.email, "user@example.com")

    def test_create_user_is_inactive_by_default(self):
        self.assertFalse(self.user.is_active)

    def test_create_user_password_is_hashed(self):
        self.assertTrue(self.user.check_password("securepassword"))
        self.assertTrue(self.user.has_usable_password())
