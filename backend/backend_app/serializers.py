"""
The serializer for the model
"""
import re
from rest_framework import serializers
from django.conf import settings
from .models import TaskItem

class TaskItemSerializer(serializers.ModelSerializer):
    """
    ModelSerializer for TaskItem
    """
    # override dt fields with preferable format
    created_dt = serializers.DateTimeField(format="%Y/%m/%d %H:%M:%S", required=False)
    wave_file_url = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    genre = serializers.SerializerMethodField()

    def get_wave_file_url(self, object):
        # task must be finished and successfully ended to have wave_file
        if object.state == 'finished' and object.ended_dt:
            request = self.context.get('request')
            # relative wave url
            rel_wave_url = settings.WAV_MEDIA_URL+'w_%s.wav'%(object.id)
            return request.build_absolute_uri(rel_wave_url)
        return None

    def get_title(self, object):
        if object.full_title:
            m = re.match(r"^(Fw:\s)?(Re:\s)?(\[(?P<genre>.*?)\])?(?P<title>.*)$", object.full_title)
            if m.group('title'):
                return m.group('title').strip()
        return None
    
    def get_genre(self, object):
        if object.full_title:
            m = re.match(r"^(Fw:\s)?(Re:\s)?(\[(?P<genre>.*?)\])?(?P<title>.*)$", object.full_title)
            if m.group('genre'):
                return m.group('genre').strip()
        return None

    class Meta:
        model = TaskItem
        fields = ('id', 'board', 'crawl_url', 'created_dt', 'state', 'title', 'genre', 'author', 'duration', 'wave_file_url')
