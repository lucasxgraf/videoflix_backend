from django.db import models


class Video(models.Model):
    class Category(models.TextChoices):
        ACTION = 'action', 'Action'
        COMEDY = 'comedy', 'Comedy'
        DRAMA = 'drama', 'Drama'
        ROMANCE = 'romance', 'Romance'
        HORROR = 'horror', 'Horror'
        SCI_FI = 'sci-fi', 'Sci-Fi'
        DOCUMENTARY = 'documentary', 'Documentary'
        ANIMATION = 'animation', 'Animation'

    class ProcessingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        DONE = 'done', 'Done'
        FAILED = 'failed', 'Failed'

    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(
        upload_to='thumbnail/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    original_video_file = models.FileField(
        upload_to='videos/')
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
