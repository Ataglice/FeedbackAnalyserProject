from rest_framework import serializers
from users.models import Feedback

class DataRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'source_id', 'external_id', 'text', 'category', 'created_at', 'send_time', 'meta_data']