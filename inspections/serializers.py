from rest_framework import serializers
from .models import InspectionZone, InspectionRecord, Commune, InspectorZoneAssignment
from users.serializers import UserDetailSerializer
from enterprises.serializers import EnterpriseSerializer


class CommuneSerializer(serializers.ModelSerializer):
    zone_name = serializers.SerializerMethodField()

    class Meta:
        model = Commune
        fields = '__all__'

    def get_zone_name(self, obj):
        return obj.zone.name if obj.zone else None


class InspectorZoneAssignmentSerializer(serializers.ModelSerializer):
    inspector_name  = serializers.SerializerMethodField()
    inspector_email = serializers.SerializerMethodField()
    role_display    = serializers.SerializerMethodField()
    zone_name       = serializers.SerializerMethodField()

    class Meta:
        model = InspectorZoneAssignment
        fields = '__all__'
        read_only_fields = ('assigned_at',)

    def get_inspector_name(self, obj):
        return obj.inspector.get_full_name()

    def get_inspector_email(self, obj):
        return obj.inspector.email

    def get_role_display(self, obj):
        return obj.get_role_display()

    def get_zone_name(self, obj):
        return obj.zone.name


class InspectionZoneSerializer(serializers.ModelSerializer):
    head_inspector_name = serializers.SerializerMethodField()
    inspectors_count    = serializers.SerializerMethodField()
    enterprises_count   = serializers.SerializerMethodField()
    communes_count      = serializers.SerializerMethodField()

    class Meta:
        model = InspectionZone
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_head_inspector_name(self, obj):
        if obj.head_inspector:
            return obj.head_inspector.get_full_name()
        return None

    def get_inspectors_count(self, obj):
        return obj.inspector_assignments.filter(is_active=True).count()

    def get_enterprises_count(self, obj):
        try:
            return obj.enterprises.count()
        except Exception:
            return 0

    def get_communes_count(self, obj):
        return obj.communes.filter(is_active=True).count()


class InspectionZoneDetailSerializer(serializers.ModelSerializer):
    head_inspector  = UserDetailSerializer(read_only=True)
    communes        = CommuneSerializer(many=True, read_only=True)
    inspector_assignments = InspectorZoneAssignmentSerializer(many=True, read_only=True)

    class Meta:
        model = InspectionZone
        fields = '__all__'


class InspectionRecordSerializer(serializers.ModelSerializer):
    inspector_name = serializers.SerializerMethodField()
    enterprise_name = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = InspectionRecord
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_inspector_name(self, obj):
        if obj.inspector:
            return obj.inspector.get_full_name()
        return None

    def get_enterprise_name(self, obj):
        return obj.enterprise.name

    def get_duration_minutes(self, obj):
        if obj.actual_date and obj.scheduled_date:
            delta = obj.actual_date - obj.scheduled_date
            return int(delta.total_seconds() / 60)
        return None


class InspectionRecordDetailSerializer(serializers.ModelSerializer):
    inspector = UserDetailSerializer(read_only=True)
    enterprise = EnterpriseSerializer(read_only=True)

    class Meta:
        model = InspectionRecord
        fields = '__all__'


class InspectionRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionRecord
        fields = [
            'enterprise', 'inspector', 'inspection_type', 'scheduled_date',
            'location', 'latitude', 'longitude'
        ]

    def create(self, validated_data):
        # Si pas d'inspecteur spécifié, assigner automatiquement
        if not validated_data.get('inspector'):
            from users.models import User
            # Trouver un inspecteur disponible dans la zone de l'entreprise
            enterprise = validated_data['enterprise']
            if enterprise.inspection_zone:
                inspectors = User.objects.filter(
                    user_type='INSPECTEUR',
                    inspector_profile__inspection_zone=enterprise.inspection_zone,
                    is_active=True
                )
                if inspectors.exists():
                    validated_data['inspector'] = inspectors.first()

        return super().create(validated_data)


class CompleteInspectionSerializer(serializers.Serializer):
    findings = serializers.CharField(required=True)
    recommendations = serializers.CharField(required=False, allow_blank=True)
    result = serializers.ChoiceField(
        choices=['COMPLIANT', 'MINOR_ISSUES', 'MAJOR_ISSUES', 'NON_COMPLIANT'],
        required=True
    )
    photos = serializers.ListField(
        child=serializers.URLField(),
        required=False
    )
    report_file = serializers.FileField(required=False)


class InspectorScheduleSerializer(serializers.Serializer):
    date = serializers.DateField()
    inspections = InspectionRecordSerializer(many=True, read_only=True)
    total = serializers.IntegerField(read_only=True)
    completed = serializers.IntegerField(read_only=True)
    pending = serializers.IntegerField(read_only=True)
