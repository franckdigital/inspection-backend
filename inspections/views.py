from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import datetime, timedelta

from .models import InspectionZone, InspectionRecord, Commune, InspectorZoneAssignment
from .serializers import (
    InspectionZoneSerializer, InspectionZoneDetailSerializer,
    InspectionRecordSerializer, InspectionRecordDetailSerializer,
    InspectionRecordCreateSerializer, CompleteInspectionSerializer,
    InspectorScheduleSerializer,
    CommuneSerializer, InspectorZoneAssignmentSerializer,
)
from enterprises.models import EnterpriseHistory


class InspectionZoneViewSet(viewsets.ModelViewSet):
    queryset = InspectionZone.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['region', 'city', 'is_active']
    search_fields = ['name', 'code', 'city', 'region']
    ordering_fields = ['name', 'created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InspectionZoneDetailSerializer
        return InspectionZoneSerializer

    @action(detail=True, methods=['get'])
    def inspectors(self, request, pk=None):
        """Liste des inspecteurs de la zone"""
        zone = self.get_object()
        inspectors = zone.inspectors.all()
        from users.serializers import UserDetailSerializer
        serializer = UserDetailSerializer(inspectors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def enterprises(self, request, pk=None):
        """Liste des entreprises de la zone"""
        zone = self.get_object()
        enterprises = zone.enterprises.all()
        from enterprises.serializers import EnterpriseSerializer
        serializer = EnterpriseSerializer(enterprises, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Statistiques de la zone"""
        zone = self.get_object()
        return Response({
            'inspectors_count': zone.inspector_assignments.filter(is_active=True).count(),
            'communes_count': zone.communes.filter(is_active=True).count(),
            'inspections_count': InspectionRecord.objects.filter(
                enterprise__inspection_zone=zone
            ).count(),
            'inspections_completed': InspectionRecord.objects.filter(
                enterprise__inspection_zone=zone,
                is_completed=True
            ).count(),
        })

    @action(detail=True, methods=['post'], url_path='assign-inspector')
    def assign_inspector(self, request, pk=None):
        """Affecter un inspecteur à la zone."""
        zone = self.get_object()
        inspector_id  = request.data.get('inspector_id')
        role          = request.data.get('role', 'MEMBER')
        languages     = request.data.get('languages_spoken', [])
        if not inspector_id:
            return Response({'detail': 'inspector_id requis.'}, status=status.HTTP_400_BAD_REQUEST)
        from users.models import User as UserModel
        try:
            inspector = UserModel.objects.get(
                id=inspector_id,
                user_type__in=['INSPECTEUR', 'CHEF_INSPECTION'],
                is_active=True,
            )
        except UserModel.DoesNotExist:
            return Response({'detail': 'Inspecteur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        assignment, created = InspectorZoneAssignment.objects.update_or_create(
            zone=zone, inspector=inspector,
            defaults={'role': role, 'languages_spoken': languages, 'is_active': True},
        )
        return Response(InspectorZoneAssignmentSerializer(assignment).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], url_path='remove-inspector/(?P<inspector_id>[^/.]+)')
    def remove_inspector(self, request, pk=None, inspector_id=None):
        """Retirer un inspecteur de la zone."""
        zone = self.get_object()
        InspectorZoneAssignment.objects.filter(zone=zone, inspector_id=inspector_id).update(is_active=False)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InspectionRecordViewSet(viewsets.ModelViewSet):
    queryset = InspectionRecord.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['inspection_type', 'result', 'is_completed', 'inspector', 'enterprise']
    search_fields = ['enterprise__name', 'location', 'findings']
    ordering_fields = ['scheduled_date', 'actual_date', 'created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return InspectionRecordCreateSerializer
        elif self.action == 'retrieve':
            return InspectionRecordDetailSerializer
        return InspectionRecordSerializer

    def get_queryset(self):
        queryset = InspectionRecord.objects.all()
        user = self.request.user

        # Filtrer selon le type d'utilisateur
        if user.user_type == 'INSPECTEUR':
            queryset = queryset.filter(inspector=user)
        elif user.user_type == 'CHEF_INSPECTION':
            # Chef voit toutes les inspections de sa zone
            if hasattr(user, 'inspector_profile') and user.inspector_profile.inspection_zone:
                queryset = queryset.filter(
                    enterprise__inspection_zone=user.inspector_profile.inspection_zone
                )

        return queryset

    def perform_create(self, serializer):
        inspection = serializer.save()

        # Créer historique entreprise
        EnterpriseHistory.objects.create(
            enterprise=inspection.enterprise,
            event_type='INSPECTION',
            description=f'Inspection programmée - {inspection.get_inspection_type_display()}',
            performed_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Terminer une inspection"""
        inspection = self.get_object()
        serializer = CompleteInspectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Mettre à jour l'inspection
        inspection.actual_date = timezone.now()
        inspection.findings = serializer.validated_data['findings']
        inspection.recommendations = serializer.validated_data.get('recommendations', '')
        inspection.result = serializer.validated_data['result']
        inspection.is_completed = True

        if 'photos' in serializer.validated_data:
            inspection.photos = serializer.validated_data['photos']

        inspection.save()

        # Mettre à jour le score de l'entreprise
        inspection.enterprise.update_compliance_score()

        # Créer historique
        EnterpriseHistory.objects.create(
            enterprise=inspection.enterprise,
            event_type='INSPECTION',
            description=f'Inspection terminée - Résultat: {inspection.get_result_display()}',
            performed_by=request.user
        )

        return Response({
            'message': 'Inspection terminée avec succès',
            'inspection': InspectionRecordDetailSerializer(inspection).data
        })

    @action(detail=True, methods=['post'])
    def upload_photos(self, request, pk=None):
        """Upload photos d'inspection"""
        inspection = self.get_object()
        photos = request.data.getlist('photos')

        # Ici vous pouvez uploader les photos vers S3 ou stockage local
        # Pour l'instant, on stocke juste les URLs
        photo_urls = []
        for photo in photos:
            # Upload logic here
            photo_urls.append(f'/media/inspections/{inspection.id}/{photo.name}')

        if not inspection.photos:
            inspection.photos = []

        inspection.photos.extend(photo_urls)
        inspection.save()

        return Response({
            'message': f'{len(photos)} photos uploadées',
            'photos': inspection.photos
        })

    @action(detail=False, methods=['get'])
    def my_schedule(self, request):
        """Planning de l'inspecteur connecté"""
        if request.user.user_type != 'INSPECTEUR':
            return Response(
                {'error': 'Seuls les inspecteurs peuvent accéder au planning'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Date du jour par défaut ou date spécifiée
        date_param = request.query_params.get('date')
        if date_param:
            date = datetime.strptime(date_param, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()

        # Inspections du jour
        inspections = InspectionRecord.objects.filter(
            inspector=request.user,
            scheduled_date__date=date
        ).order_by('scheduled_date')

        return Response({
            'date': date,
            'total': inspections.count(),
            'completed': inspections.filter(is_completed=True).count(),
            'pending': inspections.filter(is_completed=False).count(),
            'inspections': InspectionRecordSerializer(inspections, many=True).data
        })

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Inspections à venir"""
        days = int(request.query_params.get('days', 7))
        end_date = timezone.now() + timedelta(days=days)

        queryset = self.get_queryset().filter(
            scheduled_date__gte=timezone.now(),
            scheduled_date__lte=end_date,
            is_completed=False
        ).order_by('scheduled_date')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Inspections en retard"""
        queryset = self.get_queryset().filter(
            scheduled_date__lt=timezone.now(),
            is_completed=False
        ).order_by('scheduled_date')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Statistiques globales des inspections"""
        queryset = self.get_queryset()

        return Response({
            'total': queryset.count(),
            'completed': queryset.filter(is_completed=True).count(),
            'pending': queryset.filter(is_completed=False).count(),
            'by_type': {
                'ROUTINE': queryset.filter(inspection_type='ROUTINE').count(),
                'FOLLOW_UP': queryset.filter(inspection_type='FOLLOW_UP').count(),
                'COMPLAINT': queryset.filter(inspection_type='COMPLAINT').count(),
                'SPOT_CHECK': queryset.filter(inspection_type='SPOT_CHECK').count(),
            },
            'by_result': {
                'COMPLIANT': queryset.filter(result='COMPLIANT').count(),
                'MINOR_ISSUES': queryset.filter(result='MINOR_ISSUES').count(),
                'MAJOR_ISSUES': queryset.filter(result='MAJOR_ISSUES').count(),
                'NON_COMPLIANT': queryset.filter(result='NON_COMPLIANT').count(),
            }
        })

    @action(detail=False, methods=['post'])
    def check_geofence(self, request):
        """Vérifier si l'inspecteur est dans la zone"""
        from .services import is_within_geofence, find_nearest_zone

        lat = request.data.get('latitude')
        lon = request.data.get('longitude')
        zone_id = request.data.get('zone_id')

        if not lat or not lon:
            return Response(
                {'error': 'Latitude et longitude requises'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if zone_id:
            try:
                zone = InspectionZone.objects.get(id=zone_id)
                if zone.latitude and zone.longitude:
                    is_inside = is_within_geofence(lat, lon, zone.latitude, zone.longitude, radius_km=5.0)
                    return Response({
                        'is_inside_zone': is_inside,
                        'zone_name': zone.name
                    })
            except InspectionZone.DoesNotExist:
                pass

        # Trouver la zone la plus proche
        nearest_zone, distance = find_nearest_zone(lat, lon)

        return Response({
            'nearest_zone': InspectionZoneSerializer(nearest_zone).data if nearest_zone else None,
            'distance_km': round(distance, 2) if distance else None
        })

    @action(detail=False, methods=['post'])
    def nearby_enterprises(self, request):
        """Entreprises à proximité"""
        from .services import get_nearby_enterprises

        lat = request.data.get('latitude')
        lon = request.data.get('longitude')
        radius = float(request.data.get('radius_km', 5.0))

        if not lat or not lon:
            return Response(
                {'error': 'Latitude et longitude requises'},
                status=status.HTTP_400_BAD_REQUEST
            )

        enterprises = get_nearby_enterprises(lat, lon, radius)

        from enterprises.serializers import EnterpriseSerializer
        data = []
        for enterprise in enterprises:
            ent_data = EnterpriseSerializer(enterprise).data
            ent_data['distance_km'] = round(enterprise._distance, 2)
            data.append(ent_data)

        return Response({
            'count': len(data),
            'radius_km': radius,
            'enterprises': data
        })

    @action(detail=False, methods=['post'])
    def validate_presence(self, request):
        """Valider la présence de l'inspecteur sur site"""
        from .services import validate_field_presence

        inspector_lat = request.data.get('inspector_latitude')
        inspector_lon = request.data.get('inspector_longitude')
        workplace_lat = request.data.get('workplace_latitude')
        workplace_lon = request.data.get('workplace_longitude')

        if not all([inspector_lat, inspector_lon, workplace_lat, workplace_lon]):
            return Response(
                {'error': 'Toutes les coordonnées sont requises'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = validate_field_presence(
            inspector_lat, inspector_lon,
            workplace_lat, workplace_lon
        )

        return Response(result)

    @action(detail=False, methods=['get'])
    def heatmap(self, request):
        """Données heatmap des plaintes"""
        from .services import generate_heatmap_data

        complaint_type = request.query_params.get('complaint_type')
        data = generate_heatmap_data(complaint_type)

        return Response({
            'count': len(data),
            'heatmap_points': data
        })

    @action(detail=False, methods=['get'])
    def route_optimization(self, request):
        """Optimiser l'itinéraire d'inspection du jour"""
        from .services import calculate_inspection_route

        if request.user.user_type != 'INSPECTEUR':
            return Response(
                {'error': 'Seuls les inspecteurs peuvent accéder à cette fonction'},
                status=status.HTTP_403_FORBIDDEN
            )

        route = calculate_inspection_route(request.user.id)

        return Response({
            'total_inspections': len(route),
            'route': InspectionRecordSerializer(route, many=True).data
        })


# ── Communes ──────────────────────────────────────────────────────────────────

class CommuneViewSet(viewsets.ModelViewSet):
    queryset = Commune.objects.filter(is_active=True).select_related('zone')
    serializer_class = CommuneSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['zone', 'city', 'region', 'is_active']
    search_fields = ['name', 'code', 'city']


# ── Inspector zone assignments ─────────────────────────────────────────────────

class InspectorZoneAssignmentViewSet(viewsets.ModelViewSet):
    queryset = InspectorZoneAssignment.objects.filter(is_active=True).select_related('zone', 'inspector')
    serializer_class = InspectorZoneAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['zone', 'inspector', 'role', 'is_active']

