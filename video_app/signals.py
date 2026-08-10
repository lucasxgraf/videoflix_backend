import os
import shutil
import django_rq

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from video_app.models import Video
from .tasks import convert_video_to_hls
from .utils import hls_output_dir


@receiver(post_save, sender=Video)
def trigger_hls_conversion(sender, instance, created, **kwargs):
    """
    Enqueue the HLS conversion task whenever a new Video is created.
    Ignored on updates so editing metadata doesn't re-trigger conversion.
    """
    if created:
        queue = django_rq.get_queue('default')
        queue.enqueue(convert_video_to_hls, instance.id)


@receiver(post_delete, sender=Video)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Remove the original video file, the thumbnail and the whole HLS
    output directory from disk when a Video is deleted.
    """
    if instance.original_video_file:
        if os.path.isfile(instance.original_video_file.path):
            os.remove(instance.original_video_file.path)

    if instance.thumbnail:
        if os.path.isfile(instance.thumbnail.path):
            os.remove(instance.thumbnail.path)

    hls_dir = hls_output_dir(instance.id, '480p').parent
    shutil.rmtree(hls_dir, ignore_errors=True)
