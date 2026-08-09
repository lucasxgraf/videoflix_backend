from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import CustomUser
from video_app.models import Video


class VideoListTest(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'user@example.com',
            'password': 'securepassword',
        }
        
        self.user = CustomUser.objects.create_user(email=self.user_data['email'], password=self.user_data['password'], is_active=True)
        
        self.client.force_authenticate(self.user)
        
        self.url = reverse('video-list')
    
    def test_get_video_list_success(self):
        video_file = SimpleUploadedFile(
            "test_video2.mp4", b"fake video content", content_type="video/mp4"
        )
        video = Video.objects.create(
            title="Movie Title 2",
            description="Movie Description 2",
            category=Video.Category.ROMANCE,
            original_video_file=video_file,
        )

        video_file2 = SimpleUploadedFile(
            "test_video.mp4", b"fake video content", content_type="video/mp4"
        )
        thumbnail_file = SimpleUploadedFile(
            "test_thumbnail.jpeg", b"fake thumbnail content", content_type="image/jpeg"
        )
        video2 = Video.objects.create(
            title="Movie Title",
            description="Movie Description",
            category=Video.Category.DRAMA,
            original_video_file=video_file2,
            thumbnail = thumbnail_file
        )

        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Video.objects.count(), 2)
        
        self.assertEqual(response.data[0]['id'], video2.id)
        self.assertIn('created_at', response.data[0])
        self.assertEqual(response.data[0]['title'], video2.title)
        self.assertEqual(response.data[0]['description'], video2.description)
        self.assertIn(video2.thumbnail.url, response.data[0]['thumbnail_url'])
        self.assertEqual(response.data[0]['category'], video2.category)
    
    def test_get_empty_video_list_success(self):
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Video.objects.count(), 0)
    
    def test_get_video_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_video_list_thumbnail_none(self):
        video_file = SimpleUploadedFile(
            "test_video2.mp4", b"fake video content", content_type="video/mp4"
        )
        video = Video.objects.create(
            title="Movie Title 2",
            description="Movie Description 2",
            category=Video.Category.ROMANCE,
            original_video_file=video_file,
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['thumbnail_url'], None)
    
    def test_get_video_list_ordering(self):
        video_file2 = SimpleUploadedFile(
            "test_video.mp4", b"fake video content", content_type="video/mp4"
        )
        video2 = Video.objects.create(
            title="Movie Title",
            description="Movie Description",
            category=Video.Category.DRAMA,
            original_video_file=video_file2,
        )
        
        video_file = SimpleUploadedFile(
            "test_video2.mp4", b"fake video content", content_type="video/mp4"
        )
        video = Video.objects.create(
            title="Movie Title 2",
            description="Movie Description 2",
            category=Video.Category.ROMANCE,
            original_video_file=video_file,
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.data[0]['id'], video.id)
        self.assertEqual(response.data[1]['id'], video2.id)
    