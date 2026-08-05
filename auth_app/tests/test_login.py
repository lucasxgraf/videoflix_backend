from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import CustomUser

class LoginTestCase(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'user@example.com',
            'password': 'securepassword',
        }
        
        self.user = CustomUser.objects.create_user(email=self.user_data['email'], password=self.user_data['password'], is_active=True)
        
        self.url = reverse('login')
        
    def test_login_success(self):
        response = self.client.post(self.url, self.user_data, format='json')
        user = CustomUser.objects.get()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.data['detail'], 'Login successful')
        self.assertEqual(response.data['user']['id'], user.id)
        self.assertEqual(response.data['user']['email'], user.email)

        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['access_token']['httponly'])
        self.assertTrue(response.cookies['refresh_token']['httponly'])
        
    def test_login_invalid_password(self):
        user_data = self.user_data.copy()
        user_data['password'] = 'wrongpassword'
        response = self.client.post(self.url, user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access_token', response.cookies)
        self.assertNotIn('refresh_token', response.cookies)
    
    def test_login_invalid_email(self):
        user_data = self.user_data.copy()
        user_data['email'] = 'nonexistent@example.com'
        response = self.client.post(self.url, user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access_token', response.cookies)
        self.assertNotIn('refresh_token', response.cookies)
        
    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access_token', response.cookies)
        self.assertNotIn('refresh_token', response.cookies)