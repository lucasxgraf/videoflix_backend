import tempfile

from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import CustomUser
from video_app.models import Video
from video_app.utils import hls_output_dir


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class HlsSegmentTest(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'user@example.com',
            'password': 'securepassword',
        }
        self.user = CustomUser.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            is_active=True)
        self.client.force_authenticate(self.user)

        video_file = SimpleUploadedFile(
            "test_video.mp4", b"fake video content", content_type="video/mp4"
        )
        self.video = Video.objects.create(
            title="Movie Title",
            category=Video.Category.DRAMA,
            original_video_file=video_file,
        )
        self.resolution = '480p'
        self.segment = '000.ts'

        self.url = reverse(
            'hls-segment',
            kwargs={
                'movie_id': self.video.id,
                'resolution': self.resolution,
                'segment': self.segment})

    def test_hls_segment_success_(self):
        self.video.processing_status = Video.ProcessingStatus.DONE
        self.video.save()

        output_dir = hls_output_dir(self.video.id, self.resolution)
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / '000.ts'
        manifest_path.write_text('#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-ENDLIST\n')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'video/MP2T')

        content = b"".join(response.streaming_content)
        self.assertIn(b'#EXTM3U', content)

    def test_hls_segment_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_hls_segment_video_dont_exist(self):
        url = reverse('hls-segment', kwargs={'movie_id': 9999, 'resolution': self.resolution, 'segment': self.segment})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_hls_segment_wrong_processing_status(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_hls_segment_file_missing(self):
        self.video.processing_status = Video.ProcessingStatus.DONE
        self.video.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_hls_segment_path_traversal(self):
        url = reverse(
            'hls-segment',
            kwargs={
                'movie_id': self.video.id,
                'resolution': self.resolution,
                'segment': '..'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
