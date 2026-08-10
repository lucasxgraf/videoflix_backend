from rest_framework import serializers
from video_app.models import Video


class VideoSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            thumbnail_url = request.build_absolute_uri(obj.thumbnail.url)
            return thumbnail_url
        else:
            return None
