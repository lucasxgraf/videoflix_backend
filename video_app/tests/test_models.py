from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
import tempfile

from video_app.models import Video

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class VideoModelTest(TestCase):
    def setUp(self):
        self.video_file = SimpleUploadedFile(
            "test_video.mp4", b"fake video content", content_type="video/mp4"
        )
        
        self.video = Video.objects.create(
            title="Movie Title",
            category=Video.Category.ACTION,
            original_video_file=self.video_file,
        )
    
    def test_create_video_with_required_fields(self):
        self.assertEqual(self.video.title, 'Movie Title')
        self.assertEqual(Video.objects.count(), 1)
        
    def test_processing_status_defaults_to_pending(self):
        self.assertEqual(self.video.processing_status, Video.ProcessingStatus.PENDING)
        
    def test_created_at_is_auto_populated(self):
        self.assertIsNotNone(self.video.created_at)
        
    def test_invalid_category_raises_validation_error(self):
        video = Video(
            title="Test Movie",
            category="not_a_real_category",
            original_video_file=self.video_file,
        )
        with self.assertRaises(ValidationError):
            video.full_clean()
