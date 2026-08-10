from django.conf import settings
from pathlib import Path


def hls_output_dir(video_id, resolution):
    output_dir = Path(settings.MEDIA_ROOT) / 'videos' / str(video_id) / resolution

    return output_dir
