import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from video_app.ffmpeg import run_ffmpeg_hls

SAMPLE_VIDEO_PATH = Path(__file__).parent / 'fixtures' / 'sample.mp4'

class RunFfmpegHlsIntegrationTest(SimpleTestCase):
    def test_creates_valid_hls_output(self):
        output_dir = tempfile.mkdtemp()

        run_ffmpeg_hls(str(SAMPLE_VIDEO_PATH), output_dir, 640, 480)

        manifest_path = Path(output_dir) / 'index.m3u8'
        self.assertTrue(manifest_path.exists())

        ts_files = list(Path(output_dir).glob('*.ts'))
        self.assertTrue(ts_files)

        manifest_content = manifest_path.read_text()
        self.assertIn('#EXTM3U', manifest_content)