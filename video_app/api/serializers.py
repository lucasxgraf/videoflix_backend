from rest_framework import serializers
from video_app.models import Video


class VideoSerializer(serializers.ModelSerializer):
    """
    Serializes a Video for the list endpoint.
    Exposes thumbnail_url instead of the raw thumbnail field.
    """

    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']

    def get_thumbnail_url(self, obj):
        """Return the absolute thumbnail URL, or None if no thumbnail was uploaded."""
        if obj.thumbnail:
            request = self.context.get('request')
            thumbnail_url = request.build_absolute_uri(obj.thumbnail.url)
            return thumbnail_url
        else:
            return None
