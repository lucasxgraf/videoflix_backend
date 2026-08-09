from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from video_app.models import Video
from .serializers import VideoSerializer


class VideoListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VideoSerializer
    queryset = Video.objects.all().order_by('-created_at')

    def get(self, request, *args, **kwargs):
        videos = self.get_queryset()
        serializer = self.get_serializer(videos, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
        