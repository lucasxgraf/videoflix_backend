import os
from django.conf import settings

from video_app.models import Video
from video_app.ffmpeg import run_ffmpeg_hls
from video_app.utils import hls_output_dir

def convert_video_to_hls(video_id):
    video = Video.objects.get(pk=video_id)
    
    video.processing_status = Video.ProcessingStatus.PROCESSING
    video.save()

    resolutions = [
        ('480p', 854, 480), 
        ('720p', 1280, 720), 
        ('1080p', 1920, 1080)]
    
    input_path = video.original_video_file.path
    
    try:
        for resolution_name, width, height in resolutions:
            output_dir = hls_output_dir(video_id, resolution_name)
            os.makedirs(output_dir, exist_ok=True)
            run_ffmpeg_hls(input_path, output_dir, width, height)
            
        video.processing_status = Video.ProcessingStatus.DONE
        video.save()
        
    except Exception:
        video.processing_status = Video.ProcessingStatus.FAILED
        video.save()
