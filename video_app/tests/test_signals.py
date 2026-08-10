import os
import tempfile

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from unittest.mock import patch

from video_app.models import Video
from video_app.tasks import convert_video_to_hls
from video_app.utils import hls_output_dir


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class VideoSignalTests(TestCase):

    @patch('video_app.signals.django_rq.get_queue')
    def test_creating_video_enqueues_conversion(self, mock_get_queue):
        video_file = SimpleUploadedFile(
            "test_video.mp4", b"fake video content", content_type="video/mp4"
        )
        video = Video.objects.create(
            title="Movie Title",
            category=Video.Category.DRAMA,
            original_video_file=video_file,
        )
        mock_queue = mock_get_queue.return_value

        mock_queue.enqueue.assert_called_once_with(
            convert_video_to_hls, video.id)

    def test_deleting_video_and_thumbnail(self):
        video_file = SimpleUploadedFile(
            "test_video.mp4", b"fake video content", content_type="video/mp4"
        )
        thumbnail_file = SimpleUploadedFile(
            "test_thumbnail.jpeg", b"fake thumbnail content",
            content_type="image/jpeg"
        )
        video = Video.objects.create(
            title="Movie Title",
            category=Video.Category.DRAMA,
            original_video_file=video_file,
            thumbnail=thumbnail_file
        )
        resolution = '480'

        video_path = video.original_video_file.path
        thumbnail_path = video.thumbnail.path

        output_dir = hls_output_dir(video.id, resolution)
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / 'index.m3u8'
        manifest_path.write_text('#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-ENDLIST\n')

        video.delete()

        self.assertFalse(os.path.exists(video_path))
        self.assertFalse(os.path.exists(thumbnail_path))
        self.assertFalse(output_dir.exists())
