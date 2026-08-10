from django.http import FileResponse

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from video_app.models import Video
from video_app.utils import hls_output_dir, get_ready_video
from .serializers import VideoSerializer


class VideoListView(generics.GenericAPIView):
    """Lists all videos, newest first."""

    permission_classes = [IsAuthenticated]
    serializer_class = VideoSerializer
    queryset = Video.objects.all().order_by('-created_at')

    def get(self, request, *args, **kwargs):
        """Serialize and return all videos."""
        videos = self.get_queryset()
        serializer = self.get_serializer(videos, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class HlsManifestView(generics.GenericAPIView):
    """Serves the HLS master playlist (index.m3u8) for a finished video."""

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        """
        Return the index.m3u8 for the given video/resolution.
        404 if the video doesn't exist, isn't done processing, or the file is missing.
        """
        video = get_ready_video(movie_id)
        if video is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        path = hls_output_dir(movie_id, resolution) / 'index.m3u8'
        if not path.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        return FileResponse(open(path, 'rb'), content_type='application/vnd.apple.mpegurl')


class HlsSegmentView(generics.GenericAPIView):
    """Serves a single .ts segment file for a finished video."""

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        """
        Return the requested .ts segment for the given video/resolution.
        404 on path-traversal attempts, missing video, unfinished processing, or missing file.
        """
        if '..' in segment or '/' in segment:
            return Response(status=status.HTTP_404_NOT_FOUND)

        video = get_ready_video(movie_id)
        if video is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        path = hls_output_dir(movie_id, resolution) / segment
        if not path.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        return FileResponse(open(path, 'rb'), content_type='video/MP2T')
