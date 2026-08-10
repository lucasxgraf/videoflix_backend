from django.conf import settings
from pathlib import Path

from video_app.models import Video


def hls_output_dir(video_id, resolution):
    """
    Build the filesystem path for a video's HLS output at the given
    resolution, derived from the video id rather than stored on the model.
    """
    output_dir = Path(settings.MEDIA_ROOT) / 'videos' / str(video_id) / resolution

    return output_dir


def get_ready_video(movie_id):
    """
    Look up a video by id, returning it only if it exists and its
    processing_status is DONE. Returns None otherwise.
    """
    try:
        video = Video.objects.get(pk=movie_id)
    except Video.DoesNotExist:
        return None

    if video.processing_status != Video.ProcessingStatus.DONE:
        return None

    return video
