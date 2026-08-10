from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import CustomUser


class TokenRefreshViewTests(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'user@example.com',
            'password': 'securepassword',
        }

        CustomUser.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            is_active=True)

        self.client.post(reverse('login'), self.user_data, format='json')

        self.url = reverse('token_refresh')

    def test_refresh_success(self):
        access_token = self.client.cookies['access_token'].value
        response = self.client.post(self.url, format='json')

        access_token_after_refresh = self.client.cookies['access_token'].value

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(access_token, access_token_after_refresh)
        self.assertEqual(response.data['detail'], 'Token refreshed')
        self.assertIn('access', response.data)

    def test_refresh_missing_token(self):
        self.client.cookies.clear()
        response = self.client.post(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_invalid_token(self):
        self.client.cookies['refresh_token'] = 'invalid_token'
        response = self.client.post(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
