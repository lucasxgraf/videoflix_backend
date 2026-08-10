from django.http import FileResponse

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from video_app.models import Video
from video_app.utils import hls_output_dir
from .serializers import VideoSerializer
from video_app.utils import get_ready_video

class VideoListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VideoSerializer
    queryset = Video.objects.all().order_by('-created_at')

    def get(self, request, *args, **kwargs):
        videos = self.get_queryset()
        serializer = self.get_serializer(videos, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class HlsManifestView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        video = get_ready_video(movie_id)
        if video is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        path = hls_output_dir(movie_id, resolution) / 'index.m3u8'
        if not path.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        return FileResponse(open(path, 'rb'), content_type='application/vnd.apple.mpegurl')


class HlsSegmentView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        if '..' in segment or '/' in segment:
            return Response(status=status.HTTP_404_NOT_FOUND)

        video = get_ready_video(movie_id)
        if video is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        path = hls_output_dir(movie_id, resolution) / segment
        if not path.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        return FileResponse(open(path, 'rb'), content_type='video/MP2T')
