from rest_framework import serializers
from .models import Complaint, ComplaintDocument, ComplaintComment, ComplaintStatusHistory, ComplaintNotification
from users.serializers import UserDetailSerializer


class ComplaintDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ComplaintDocument
        fields = '__all__'

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class ComplaintCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = ComplaintComment
        fields = '__all__'

    def get_author_name(self, obj):
        return obj.author.get_full_name()


class ComplaintStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ComplaintStatusHistory
        fields = '__all__'

    def get_changed_by_name(self, obj):
        if obj.changed_by:
            return obj.changed_by.get_full_name()
        return None


class ComplaintSerializer(serializers.ModelSerializer):
    complainant_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = '__all__'
        read_only_fields = ('complaint_number', 'created_at', 'updated_at')

    def get_complainant_name(self, obj):
        return obj.complainant.get_full_name()

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name()
        return None


class ComplaintDetailSerializer(serializers.ModelSerializer):
    complainant = UserDetailSerializer(read_only=True)
    assigned_to = UserDetailSerializer(read_only=True)
    documents = ComplaintDocumentSerializer(many=True, read_only=True)
    comments = ComplaintCommentSerializer(many=True, read_only=True)
    status_history = ComplaintStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Complaint
        fields = '__all__'


class ComplaintCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = [
            'complaint_type', 'subject', 'description', 'enterprise',
            'employer_name', 'workplace_address', 'workplace_latitude',
            'workplace_longitude', 'incident_date'
        ]

    def create(self, validated_data):
        validated_data['complainant'] = self.context['request'].user
        complaint = Complaint.objects.create(**validated_data)
        complaint.assign_to_zone()
        return complaint


class ComplaintNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintNotification
        fields = '__all__'
