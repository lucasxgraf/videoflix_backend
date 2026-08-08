import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from video_app.models import Video
from video_app.tasks import convert_video_to_hls


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ConvertVideoToHlsTest(TestCase):
    def setUp(self):
        video_file = SimpleUploadedFile(
            "test_video.mp4", b"fake video content", content_type="video/mp4"
        )
        self.video = Video.objects.create(
            title="Movie Title",
            category=Video.Category.ACTION,
            original_video_file=video_file,
        )

    @patch('video_app.tasks.run_ffmpeg_hls')
    def test_status_is_done_after_successful_conversion(self, mock_run_ffmpeg):
        convert_video_to_hls(self.video.id)
        self.video.refresh_from_db()
        
        self.assertEqual(self.video.processing_status, Video.ProcessingStatus.DONE)

    @patch('video_app.tasks.run_ffmpeg_hls')
    def test_run_ffmpeg_called_three_times(self, mock_run_ffmpeg):
        convert_video_to_hls(self.video.id)
        
        self.assertEqual(mock_run_ffmpeg.call_count, 3)

    @patch('video_app.tasks.run_ffmpeg_hls')
    def test_status_is_failed_when_ffmpeg_raises(self, mock_run_ffmpeg):
        mock_run_ffmpeg.side_effect = Exception("ffmpeg failed")
        convert_video_to_hls(self.video.id)

        self.video.refresh_from_db()
        self.assertEqual(self.video.processing_status, Video.ProcessingStatus.FAILED)
        
    @patch('video_app.tasks.run_ffmpeg_hls')
    def test_correct_resolution_height_and_width(self, mock_run_ffmpeg):
        convert_video_to_hls(self.video.id)
        
        first_call = mock_run_ffmpeg.call_args_list[0]
        self.assertEqual(first_call.args[2], 854)
        self.assertEqual(first_call.args[3], 480)
        
        second_call = mock_run_ffmpeg.call_args_list[1]
        self.assertEqual(second_call.args[2], 1280)
        self.assertEqual(second_call.args[3], 720)
        
        third_call = mock_run_ffmpeg.call_args_list[2]
        self.assertEqual(third_call.args[2], 1920)
        self.assertEqual(third_call.args[3], 1080)