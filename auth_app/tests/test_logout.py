from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import CustomUser


class LogoutTestCase(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'user@example.com',
            'password': 'securepassword',
        }

        self.user = CustomUser.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            is_active=True)

        self.client.post(reverse('login'), self.user_data, format='json')

        self.url = reverse('logout')

    def test_logout_success(self):
        response = self.client.post(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['detail'],
            'Logout successful! All Tokens will be deleted. Refresh token is now invalid.')
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')

    def test_logout_unauthenticated(self):
        self.client.cookies.clear()
        response = self.client.post(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_invalid_refresh_token_cookie(self):
        self.client.cookies['refresh_token'] = 'invalid_token'
        response = self.client.post(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_token_blacklisted(self):
        token = self.client.cookies['refresh_token'].value

        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.cookies['refresh_token'] = token
        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
