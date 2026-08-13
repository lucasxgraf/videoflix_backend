import os
import logging
import tempfile

from django.core.files import File

from video_app.models import Video
from video_app.ffmpeg import run_ffmpeg_hls, extract_thumbnail
from video_app.utils import hls_output_dir

logger = logging.getLogger(__name__)


def convert_video_to_hls(video_id):
    """
    Convert the given video to HLS in all target resolutions and update
    its processing_status accordingly (processing -> done/failed).
    """
    video = Video.objects.get(pk=video_id)

    video.processing_status = Video.ProcessingStatus.PROCESSING
    video.save()

    if not video.thumbnail:
        try:
            _generate_thumbnail(video)
        except Exception:
            logger.exception("Thumbnail generation failed for video %s", video_id)

    try:
        _convert_all_resolutions(video)
        video.processing_status = Video.ProcessingStatus.DONE
        video.save()
    except Exception:
        logger.exception("HLS conversion failed for video %s", video_id)
        video.processing_status = Video.ProcessingStatus.FAILED
        video.save()


def _generate_thumbnail(video):
    """Extract a frame from the source video and use it as the thumbnail."""
    input_path = video.original_video_file.path

    with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
        extract_thumbnail(input_path, tmp_file.name, second=1)
        video.thumbnail.save(
            f'{video.id}.jpg', File(tmp_file), save=False)
    video.save()


def _convert_all_resolutions(video):
    """Run the ffmpeg HLS conversion for every target resolution."""
    input_path = video.original_video_file.path
    
    resolutions = [
        ('480p', 854, 480),
        ('720p', 1280, 720),
        ('1080p', 1920, 1080),
    ]
    
    for resolution_name, width, height in resolutions:
        output_dir = hls_output_dir(video.id, resolution_name)
        os.makedirs(output_dir, exist_ok=True)
        run_ffmpeg_hls(input_path, output_dir, width, height)