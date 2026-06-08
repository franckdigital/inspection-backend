from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from math import radians, cos, sin, asin, sqrt

from .models import (
    DomesticWorker, DomesticEmployer, DomesticContract,
    TimeTracking, MonthlyPayslip, LeaveRequest, VoiceComplaint, OvertimeSession,
    FieldVisit,
)
from .serializers import (
    DomesticWorkerSerializer, DomesticEmployerSerializer,
    DomesticContractSerializer, SignContractSerializer,
    TimeTrackingSerializer, CheckInSerializer, CheckOutSerializer,
    MonthlyPayslipSerializer, GeneratePayslipSerializer,
    LeaveRequestSerializer, ApproveRejectLeaveSerializer,
    VoiceComplaintSerializer, VoiceComplaintCreateSerializer,
    InspectorRespondSerializer, OvertimeSessionSerializer,
    FieldVisitSerializer, RecordGPSSerializer,
)

# ── Constantes RG-DOM ─────────────────────────────────────────────────────────

SMIG_CI_MONTHLY = Decimal('75000')   # SMIG Côte d'Ivoire en FCFA
MAX_DAILY_HOURS = Decimal('10')      # RG-DOM-004/005
MAX_WEEKLY_HOURS = Decimal('60')     # RG-DOM-005
GEOFENCE_RADIUS_METERS = 500         # RG-DOM-003


def haversine_meters(lat1, lon1, lat2, lon2) -> float:
    """Distance entre deux coordonnées GPS en mètres."""
    R = 6_371_000
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return R * 2 * asin(sqrt(a))


def is_admin_or_inspector(user) -> bool:
    return user.user_type in [
        'ADMIN', 'INSPECTEUR', 'CHEF_INSPECTION', 'DIRECTEUR_REGIONAL', 'DIRECTEUR_GENERAL'
    ]


def _auto_assign_inspector(contract: DomesticContract) -> None:
    """
    Affecte l'inspecteur compétent à un contrat qui devient ACTIVE.
    Priorité : chef de la zone → premier inspecteur actif.
    """
    if contract.inspector:
        return  # déjà assigné

    from inspections.models import InspectionZone
    from users.models import User as UserModel

    # Cherche la commune du worker (champ city sur l'utilisateur)
    city = getattr(contract.worker.user, 'city', '') or ''

    if city:
        zone = InspectionZone.objects.filter(city__icontains=city, is_active=True).first()
        if zone and zone.head_inspector and zone.head_inspector.is_active:
            contract.inspector = zone.head_inspector
            return

    # Fallback : premier inspecteur actif en base
    fallback = UserModel.objects.filter(user_type='INSPECTEUR', is_active=True).first()
    if fallback:
        contract.inspector = fallback


def _resolve_inspector_for_complaint(worker, commune: str):
    """
    Retourne l'inspecteur à affecter à une plainte vocale.
    Ordre de priorité :
    1. L'inspecteur déjà lié au contrat actif du worker
    2. Le chef de la zone couvrant la commune de la plainte
    3. Premier inspecteur actif en base
    """
    from inspections.models import InspectionZone
    from users.models import User as UserModel

    # 1. Inspecteur du contrat actif
    active_contract = worker.contracts.filter(status='ACTIVE').select_related('inspector').first()
    if active_contract and active_contract.inspector and active_contract.inspector.is_active:
        return active_contract.inspector

    # 2. Chef de zone selon la commune
    if commune:
        zone = InspectionZone.objects.filter(city__icontains=commune, is_active=True).first()
        if zone and zone.head_inspector and zone.head_inspector.is_active:
            return zone.head_inspector

    # 3. Fallback
    return UserModel.objects.filter(user_type='INSPECTEUR', is_active=True).first()


# ── Workers ───────────────────────────────────────────────────────────────────

class DomesticWorkerViewSet(viewsets.ModelViewSet):
    serializer_class = DomesticWorkerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['specialization', 'is_available']

    def get_queryset(self):
        user = self.request.user
        if is_admin_or_inspector(user):
            return DomesticWorker.objects.all()
        if user.user_type in ('EMPLOYE', 'EMPLOYE_MAISON'):
            return DomesticWorker.objects.filter(user=user)
        if user.user_type == 'EMPLOYEUR':
            employer_ids = DomesticEmployer.objects.filter(user=user).values_list('id', flat=True)
            worker_ids = DomesticContract.objects.filter(employer_id__in=employer_ids).values_list('worker_id', flat=True)
            return DomesticWorker.objects.filter(id__in=worker_ids)
        return DomesticWorker.objects.none()

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Chercher un travailleur par email ou numéro de téléphone."""
        email = request.query_params.get('email', '').strip()
        phone = request.query_params.get('phone', '').strip()

        if not email and not phone:
            return Response(
                {'detail': 'Paramètre email ou phone requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from users.models import User
            if email:
                user = User.objects.get(email__iexact=email, user_type='EMPLOYE_MAISON')
            else:
                # Accepter avec ou sans préfixe +225
                normalized = phone.replace(' ', '').replace('-', '')
                user = User.objects.get(phone_number=normalized, user_type='EMPLOYE_MAISON')
            worker = DomesticWorker.objects.get(user=user)
            return Response({
                'id': worker.id,
                'name': user.get_full_name(),
                'email': user.email,
                'phone': user.phone_number or '',
                'specialization': worker.specialization,
                'specialization_display': worker.get_specialization_display(),
                'years_experience': worker.years_experience,
                'is_available': worker.is_available,
            })
        except Exception:
            label = 'cet email' if email else 'ce numéro de téléphone'
            return Response(
                {'detail': f'Aucun employé de maison trouvé avec {label}.'},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Profil DomesticWorker de l'utilisateur connecté."""
        try:
            worker = DomesticWorker.objects.get(user=request.user)
        except DomesticWorker.DoesNotExist:
            return Response(
                {'error': 'Profil non trouvé', 'setup_required': True},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.method == 'GET':
            return Response(DomesticWorkerSerializer(worker).data)
        serializer = DomesticWorkerSerializer(worker, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def available(self, request):
        workers = DomesticWorker.objects.filter(is_available=True)
        return Response(self.get_serializer(workers, many=True).data)


# ── Employers ─────────────────────────────────────────────────────────────────

class DomesticEmployerViewSet(viewsets.ModelViewSet):
    serializer_class = DomesticEmployerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if is_admin_or_inspector(user):
            return DomesticEmployer.objects.all()
        if user.user_type == 'EMPLOYEUR':
            return DomesticEmployer.objects.filter(user=user)
        if user.user_type == 'EMPLOYE':
            worker_ids = DomesticWorker.objects.filter(user=user).values_list('id', flat=True)
            employer_ids = DomesticContract.objects.filter(
                worker_id__in=worker_ids
            ).values_list('employer_id', flat=True)
            return DomesticEmployer.objects.filter(id__in=employer_ids)
        return DomesticEmployer.objects.none()

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Profil DomesticEmployer de l'utilisateur connecté."""
        try:
            employer = DomesticEmployer.objects.get(user=request.user)
        except DomesticEmployer.DoesNotExist:
            return Response(
                {'error': 'Profil non trouvé', 'setup_required': True},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.method == 'GET':
            return Response(DomesticEmployerSerializer(employer).data)
        serializer = DomesticEmployerSerializer(employer, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ── Contracts ─────────────────────────────────────────────────────────────────

class DomesticContractViewSet(viewsets.ModelViewSet):
    serializer_class = DomesticContractSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'worker', 'employer']

    def perform_create(self, serializer):
        """Auto-assigne l'employer à partir de l'utilisateur connecté."""
        if self.request.user.user_type == 'EMPLOYEUR':
            employer = DomesticEmployer.objects.get(user=self.request.user)
            serializer.save(employer=employer)
        else:
            serializer.save()

    def get_queryset(self):
        user = self.request.user
        if is_admin_or_inspector(user):
            return DomesticContract.objects.all()
        if user.user_type in ('EMPLOYE', 'EMPLOYE_MAISON'):
            worker_ids = DomesticWorker.objects.filter(user=user).values_list('id', flat=True)
            return DomesticContract.objects.filter(worker_id__in=worker_ids)
        if user.user_type == 'EMPLOYEUR':
            employer_ids = DomesticEmployer.objects.filter(user=user).values_list('id', flat=True)
            return DomesticContract.objects.filter(employer_id__in=employer_ids)
        return DomesticContract.objects.none()

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        contract = self.get_object()
        serializer = SignContractSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role = serializer.validated_data['signer_role']
        if role == 'worker':
            contract.worker_signature = serializer.validated_data['signature_image']
        elif role == 'employer':
            contract.employer_signature = serializer.validated_data['signature_image']

        if contract.is_fully_signed() and contract.status == 'PENDING_SIGNATURE':
            contract.status = 'ACTIVE'
            contract.signed_at = timezone.now()
            _auto_assign_inspector(contract)

        contract.save()
        return Response({
            'message': f'Signature {role} enregistrée',
            'is_fully_signed': contract.is_fully_signed(),
            'status': contract.status,
            'inspector': contract.inspector.get_full_name() if contract.inspector else None,
        })

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        contract = self.get_object()
        contract.status = 'ACTIVE'
        _auto_assign_inspector(contract)
        contract.save()
        return Response({
            'message': 'Contrat activé',
            'inspector': contract.inspector.get_full_name() if contract.inspector else None,
        })

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        contract = self.get_object()
        contract.status = 'TERMINATED'
        contract.end_date = timezone.now().date()
        contract.save()
        return Response({'message': 'Contrat terminé'})

    @action(detail=True, methods=['post'], url_path='assign-inspector')
    def assign_inspector(self, request, pk=None):
        """Admin : affecter manuellement un inspecteur à un contrat."""
        if request.user.user_type not in ('ADMIN', 'CHEF_INSPECTION', 'DIRECTEUR_REGIONAL', 'DIRECTEUR_GENERAL'):
            return Response({'detail': 'Accès réservé aux administrateurs.'}, status=status.HTTP_403_FORBIDDEN)
        contract = self.get_object()
        inspector_id = request.data.get('inspector_id')
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
        contract.inspector = inspector
        contract.save(update_fields=['inspector'])
        return Response({
            'message': 'Inspecteur affecté avec succès.',
            'inspector': inspector.get_full_name(),
            'inspector_id': inspector.id,
        })

    @action(detail=False, methods=['get'], url_path='unassigned')
    def unassigned(self, request):
        """Liste des contrats actifs sans inspecteur assigné."""
        if request.user.user_type not in ('ADMIN', 'CHEF_INSPECTION', 'DIRECTEUR_REGIONAL', 'DIRECTEUR_GENERAL'):
            return Response({'detail': 'Accès réservé.'}, status=status.HTTP_403_FORBIDDEN)
        contracts = DomesticContract.objects.filter(
            status='ACTIVE', inspector__isnull=True
        ).select_related('worker__user', 'employer__user')
        return Response(DomesticContractSerializer(contracts, many=True).data)


# ── Time Tracking (Pointage) ──────────────────────────────────────────────────

class TimeTrackingViewSet(viewsets.ModelViewSet):
    serializer_class = TimeTrackingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contract', 'date', 'is_validated']

    def get_queryset(self):
        user = self.request.user
        if is_admin_or_inspector(user):
            return TimeTracking.objects.all()
        if user.user_type in ('EMPLOYE', 'EMPLOYE_MAISON'):
            worker_ids = DomesticWorker.objects.filter(user=user).values_list('id', flat=True)
            return TimeTracking.objects.filter(contract__worker_id__in=worker_ids)
        if user.user_type == 'EMPLOYEUR':
            employer_ids = DomesticEmployer.objects.filter(user=user).values_list('id', flat=True)
            return TimeTracking.objects.filter(contract__employer_id__in=employer_ids)
        return TimeTracking.objects.none()

    @action(detail=False, methods=['post'])
    def checkin(self, request):
        """
        Pointer l'arrivée avec validation géographique (RG-DOM-002, RG-DOM-003).
        Rejeté si l'employé est hors de la zone autorisée (500 m autour du domicile).
        """
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            contract = DomesticContract.objects.get(id=serializer.validated_data['contract_id'])
        except DomesticContract.DoesNotExist:
            return Response({'error': 'Contrat introuvable'}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()

        # RG-DOM-003 : validation géofencing
        employer = contract.employer
        if employer.latitude and employer.longitude:
            lat = serializer.validated_data['latitude']
            lon = serializer.validated_data['longitude']
            distance = haversine_meters(lat, lon, employer.latitude, employer.longitude)
            if distance > GEOFENCE_RADIUS_METERS:
                return Response({
                    'error': (
                        f'Vous êtes trop loin du lieu de travail ({distance:.0f} m). '
                        f'Zone autorisée : {GEOFENCE_RADIUS_METERS} m.'
                    ),
                    'distance_meters': round(distance),
                    'geofence_radius': GEOFENCE_RADIUS_METERS,
                    'outside_zone': True,
                }, status=status.HTTP_400_BAD_REQUEST)

        existing = TimeTracking.objects.filter(contract=contract, date=today).first()
        if existing:
            return Response(
                {'error': 'Pointage déjà effectué aujourd\'hui'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tracking = TimeTracking.objects.create(
            contract=contract,
            date=today,
            check_in_time=timezone.now(),
            check_in_latitude=serializer.validated_data['latitude'],
            check_in_longitude=serializer.validated_data['longitude'],
            check_in_address=serializer.validated_data.get('address', '')
        )
        return Response(TimeTrackingSerializer(tracking).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        """Pointer le départ — calcul automatique des heures sup (RG-DOM-004)."""
        tracking = self.get_object()
        serializer = CheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if tracking.check_out_time:
            return Response({'error': 'Départ déjà pointé'}, status=status.HTTP_400_BAD_REQUEST)

        tracking.check_out_time = timezone.now()
        tracking.check_out_latitude = serializer.validated_data['latitude']
        tracking.check_out_longitude = serializer.validated_data['longitude']
        tracking.check_out_address = serializer.validated_data.get('address', '')
        tracking.notes = serializer.validated_data.get('notes', '')
        tracking.calculate_hours()

        return Response(TimeTrackingSerializer(tracking).data)

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        tracking = self.get_object()
        tracking.is_validated = True
        tracking.save()
        return Response({'message': 'Pointage validé'})

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        contract_id = request.query_params.get('contract_id')
        month = request.query_params.get('month')

        if not contract_id or not month:
            return Response({'error': 'contract_id et month requis'}, status=status.HTTP_400_BAD_REQUEST)

        month_date = datetime.strptime(month, '%Y-%m-%d').date()
        first_day = month_date.replace(day=1)
        last_day = (first_day + relativedelta(months=1)) - relativedelta(days=1)

        trackings = TimeTracking.objects.filter(
            contract_id=contract_id,
            date__gte=first_day,
            date__lte=last_day
        )

        total_hours = sum([t.hours_worked for t in trackings], Decimal('0'))
        total_overtime = sum([t.overtime_hours for t in trackings], Decimal('0'))

        return Response({
            'month': month,
            'total_days': trackings.count(),
            'total_hours': float(total_hours),
            'total_overtime': float(total_overtime),
            'trackings': TimeTrackingSerializer(trackings, many=True).data
        })

    @action(detail=False, methods=['get'])
    def abuse_alerts(self, request):
        """
        Détection automatique d'abus (RG-DOM-005).
        Analyse les 30 derniers jours pour le contrat donné.
        """
        contract_id = request.query_params.get('contract_id')
        if not contract_id:
            return Response({'error': 'contract_id requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            contract = DomesticContract.objects.get(id=contract_id)
        except DomesticContract.DoesNotExist:
            return Response({'error': 'Contrat introuvable'}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()
        since = today - timedelta(days=30)
        trackings = list(TimeTracking.objects.filter(
            contract=contract, date__gte=since, date__lte=today
        ))

        alerts = []

        # Journées > 10h
        for t in trackings:
            if t.hours_worked and t.hours_worked > MAX_DAILY_HOURS:
                alerts.append({
                    'type': 'EXCESSIVE_DAILY_HOURS',
                    'severity': 'HIGH',
                    'date': str(t.date),
                    'message': (
                        f'Journée du {t.date.strftime("%d/%m/%Y")} : '
                        f'{float(t.hours_worked):.1f}h travaillées (max légal : {MAX_DAILY_HOURS}h)'
                    ),
                })

        # Semaines > 60h
        weeks: dict = {}
        for t in trackings:
            week_start = t.date - timedelta(days=t.date.weekday())
            weeks.setdefault(week_start, Decimal('0'))
            weeks[week_start] += t.hours_worked or Decimal('0')

        for week_start, total in weeks.items():
            if total > MAX_WEEKLY_HOURS:
                alerts.append({
                    'type': 'EXCESSIVE_WEEKLY_HOURS',
                    'severity': 'HIGH',
                    'week_start': str(week_start),
                    'message': (
                        f'Semaine du {week_start.strftime("%d/%m/%Y")} : '
                        f'{float(total):.1f}h (max légal : {MAX_WEEKLY_HOURS}h)'
                    ),
                })

        # 7 jours consécutifs sans repos
        work_dates = sorted([t.date for t in trackings])
        for i in range(len(work_dates) - 6):
            window = work_dates[i:i + 7]
            if (window[-1] - window[0]).days == 6:
                alerts.append({
                    'type': 'NO_REST',
                    'severity': 'CRITICAL',
                    'message': (
                        f'7 jours consécutifs sans repos '
                        f'(du {window[0].strftime("%d/%m/%Y")} au {window[-1].strftime("%d/%m/%Y")})'
                    ),
                })

        # Salaire inférieur au SMIG
        if contract.salary < SMIG_CI_MONTHLY:
            alerts.append({
                'type': 'BELOW_MINIMUM_WAGE',
                'severity': 'CRITICAL',
                'message': (
                    f'Salaire ({float(contract.salary):,.0f} FCFA) inférieur au SMIG '
                    f'({float(SMIG_CI_MONTHLY):,.0f} FCFA/mois)'
                ),
            })

        return Response({
            'contract_id': int(contract_id),
            'period': {'from': str(since), 'to': str(today)},
            'alert_count': len(alerts),
            'alerts': alerts,
        })

    @action(detail=False, methods=['get'], url_path='address-book')
    def address_book(self, request):
        """
        Carnet d'adresses des employés supervisés par l'inspecteur.
        Retourne la dernière position GPS connue (dernier pointage) pour chaque employé,
        groupée par commune / zone géographique.
        """
        user = request.user
        if not is_admin_or_inspector(user):
            return Response({'error': 'Accès réservé aux inspecteurs'}, status=status.HTTP_403_FORBIDDEN)

        if user.user_type == 'ADMIN':
            contracts = DomesticContract.objects.filter(status='ACTIVE').select_related(
                'worker__user', 'employer', 'inspector'
            )
        else:
            contracts = DomesticContract.objects.filter(
                inspector=user, status='ACTIVE'
            ).select_related('worker__user', 'employer')

        from inspections.models import InspectionZone

        result = []
        for contract in contracts:
            latest = (
                TimeTracking.objects
                .filter(contract=contract)
                .order_by('-check_in_time')
                .first()
            )
            total = TimeTracking.objects.filter(contract=contract).count()

            # Commune : extraite de l'adresse ou ville de l'employeur
            commune = ''
            if latest and latest.check_in_address:
                parts = [p.strip() for p in latest.check_in_address.split(',')]
                commune = parts[-1] if parts else ''
            if not commune:
                commune = contract.employer.city or ''

            # Zone d'inspection correspondante
            zone_name = ''
            if commune:
                zone = InspectionZone.objects.filter(
                    city__icontains=commune, is_active=True
                ).first()
                if zone:
                    zone_name = zone.name

            result.append({
                'worker_id':            contract.worker.id,
                'worker_name':          contract.worker.user.get_full_name(),
                'specialization':       contract.worker.specialization,
                'specialization_display': contract.worker.get_specialization_display(),
                'contract_id':          contract.id,
                'employer_name':        contract.employer.user.get_full_name(),
                'employer_address':     contract.employer.address,
                'commune':              commune,
                'zone_name':            zone_name,
                'last_checkin_date':    latest.date.isoformat() if latest else None,
                'last_checkin_time':    latest.check_in_time.isoformat() if latest else None,
                'last_address':         latest.check_in_address if latest else '',
                'latitude':  float(latest.check_in_latitude)  if latest and latest.check_in_latitude  else None,
                'longitude': float(latest.check_in_longitude) if latest and latest.check_in_longitude else None,
                'total_checkins':       total,
            })

        result.sort(key=lambda x: (x['commune'] or 'zzz', x['worker_name']))
        return Response(result)


# ── Payslips ──────────────────────────────────────────────────────────────────

class MonthlyPayslipViewSet(viewsets.ModelViewSet):
    serializer_class = MonthlyPayslipSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contract', 'status', 'month']

    def get_queryset(self):
        user = self.request.user
        if is_admin_or_inspector(user):
            return MonthlyPayslip.objects.all()
        if user.user_type in ('EMPLOYE', 'EMPLOYE_MAISON'):
            worker_ids = DomesticWorker.objects.filter(user=user).values_list('id', flat=True)
            return MonthlyPayslip.objects.filter(contract__worker_id__in=worker_ids)
        if user.user_type == 'EMPLOYEUR':
            employer_ids = DomesticEmployer.objects.filter(user=user).values_list('id', flat=True)
            return MonthlyPayslip.objects.filter(contract__employer_id__in=employer_ids)
        return MonthlyPayslip.objects.none()

    @action(detail=False, methods=['post'])
    def generate(self, request):
        serializer = GeneratePayslipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            contract = DomesticContract.objects.get(id=serializer.validated_data['contract_id'])
        except DomesticContract.DoesNotExist:
            return Response({'error': 'Contrat introuvable'}, status=status.HTTP_404_NOT_FOUND)

        month_date = serializer.validated_data['month']
        first_day = month_date.replace(day=1)
        last_day = (first_day + relativedelta(months=1)) - relativedelta(days=1)

        trackings = TimeTracking.objects.filter(
            contract=contract,
            date__gte=first_day,
            date__lte=last_day,
            is_validated=True
        )

        regular_hours = sum([t.hours_worked - t.overtime_hours for t in trackings], Decimal('0'))
        overtime_hours = sum([t.overtime_hours for t in trackings], Decimal('0'))
        hourly_rate = contract.salary / Decimal('160')
        overtime_rate = hourly_rate * Decimal('1.5')

        payslip, created = MonthlyPayslip.objects.get_or_create(
            contract=contract,
            month=first_day,
            defaults={
                'base_salary': contract.salary,
                'transportation_allowance': contract.transportation_allowance,
                'status': 'DRAFT',
                'gross_pay': contract.salary,
                'total_deductions': Decimal('0'),
                'net_pay': contract.salary,
            }
        )

        payslip.regular_hours = regular_hours
        payslip.overtime_hours = overtime_hours
        payslip.overtime_pay = overtime_hours * overtime_rate
        payslip.bonuses = serializer.validated_data.get('bonuses', Decimal('0'))
        payslip.other_deductions = serializer.validated_data.get('other_deductions', Decimal('0'))
        payslip.social_security = (payslip.base_salary + payslip.overtime_pay) * Decimal('0.025')
        payslip.calculate_totals()
        payslip.status = 'GENERATED'

        return Response({
            'message': 'Bulletin généré',
            'payslip': MonthlyPayslipSerializer(payslip).data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        payslip = self.get_object()
        payslip.status = 'PAID'
        payslip.payment_date = timezone.now().date()
        payslip.payment_method = request.data.get('payment_method', 'CASH')
        payslip.save()
        return Response({'message': 'Bulletin marqué comme payé'})


# ── Leave Requests ────────────────────────────────────────────────────────────

class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contract', 'status', 'leave_type']

    def get_queryset(self):
        user = self.request.user
        if is_admin_or_inspector(user):
            return LeaveRequest.objects.all()
        if user.user_type in ('EMPLOYE', 'EMPLOYE_MAISON'):
            worker_ids = DomesticWorker.objects.filter(user=user).values_list('id', flat=True)
            return LeaveRequest.objects.filter(contract__worker_id__in=worker_ids)
        if user.user_type == 'EMPLOYEUR':
            employer_ids = DomesticEmployer.objects.filter(user=user).values_list('id', flat=True)
            return LeaveRequest.objects.filter(contract__employer_id__in=employer_ids)
        return LeaveRequest.objects.none()

    @action(detail=True, methods=['post'])
    def approve_reject(self, request, pk=None):
        leave_request = self.get_object()
        serializer = ApproveRejectLeaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        leave_request.status = serializer.validated_data['status']
        leave_request.response_comment = serializer.validated_data.get('response_comment', '')
        leave_request.responded_at = timezone.now()
        leave_request.save()

        return Response({'message': f'Demande {leave_request.get_status_display().lower()}'})


# ── OvertimeSession ──────────────────────────────────────────────────────────

class OvertimeSessionViewSet(viewsets.GenericViewSet):
    serializer_class = OvertimeSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_today_tracking(self, user):
        try:
            worker = DomesticWorker.objects.get(user=user)
            contract = worker.contracts.filter(status='ACTIVE').first()
            if not contract:
                return None, None, 'Aucun contrat actif.'
            today = timezone.now().date()
            tracking = TimeTracking.objects.filter(contract=contract, date=today).first()
            if not tracking:
                return None, None, 'Aucun pointage d\'arrivée aujourd\'hui.'
            return worker, tracking, None
        except DomesticWorker.DoesNotExist:
            return None, None, 'Profil introuvable.'

    def list(self, request):
        _, tracking, err = self._get_today_tracking(request.user)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        date_str = request.query_params.get('date')
        if date_str:
            try:
                from datetime import date as date_cls
                d = date_cls.fromisoformat(date_str)
                worker = DomesticWorker.objects.get(user=request.user)
                contract = worker.contracts.filter(status='ACTIVE').first()
                tracking = TimeTracking.objects.filter(contract=contract, date=d).first()
                if not tracking:
                    return Response([])
            except Exception:
                return Response({'detail': 'Date invalide.'}, status=400)
        sessions = tracking.overtime_sessions.all()
        return Response(OvertimeSessionSerializer(sessions, many=True).data)

    @action(detail=False, methods=['post'])
    def start(self, request):
        _, tracking, err = self._get_today_tracking(request.user)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        if not tracking.check_out_time:
            return Response({'detail': 'Pointez le départ avant de déclarer des heures supplémentaires.'}, status=400)
        active = tracking.overtime_sessions.filter(is_active=True).first()
        if active:
            return Response({'detail': 'Une session d\'heures supplémentaires est déjà en cours.'}, status=400)
        reason = request.data.get('reason', '')
        session = OvertimeSession.objects.create(
            tracking=tracking,
            start_time=timezone.now(),
            reason=reason,
        )
        return Response(OvertimeSessionSerializer(session).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        try:
            session = OvertimeSession.objects.get(pk=pk)
        except OvertimeSession.DoesNotExist:
            return Response({'detail': 'Session introuvable.'}, status=404)
        if not session.is_active:
            return Response({'detail': 'Session déjà terminée.'}, status=400)
        session.stop()
        return Response(OvertimeSessionSerializer(session).data)


# ── VoiceComplaint ────────────────────────────────────────────────────────────

class VoiceComplaintViewSet(viewsets.ModelViewSet):
    serializer_class = VoiceComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        if is_admin_or_inspector(user):
            if user.user_type in ('INSPECTEUR', 'CHEF_INSPECTION'):
                return VoiceComplaint.objects.filter(
                    Q(assigned_inspector=user) | Q(assistance_inspector=user)
                )
            return VoiceComplaint.objects.all()
        if user.user_type in ('EMPLOYE_MAISON', 'EMPLOYE'):
            try:
                worker = DomesticWorker.objects.get(user=user)
                return VoiceComplaint.objects.filter(worker=worker)
            except DomesticWorker.DoesNotExist:
                return VoiceComplaint.objects.none()
        return VoiceComplaint.objects.none()

    def create(self, request, *args, **kwargs):
        if request.user.user_type != 'EMPLOYE_MAISON':
            return Response({'detail': 'Réservé aux employées de maison.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            worker = DomesticWorker.objects.get(user=request.user)
        except DomesticWorker.DoesNotExist:
            return Response({'detail': 'Profil d\'employée de maison introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        s = VoiceComplaintCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        selected_lang = d.get('selected_language', '')
        vc = VoiceComplaint(
            worker=worker,
            audio_file=d['audio_file'],
            duration_seconds=d.get('duration_seconds', 0),
            selected_language=selected_lang,
            detected_language=selected_lang or d.get('detected_language', ''),
            language_confidence=d.get('language_confidence', 0.0),
            commune=d.get('commune', ''),
            latitude=d.get('latitude'),
            longitude=d.get('longitude'),
            status='PENDING',
            transcription_status='PENDING',
        )

        # Résoudre l'inspecteur compétent (contrat actif → zone → fallback)
        commune = d.get('commune', '')
        inspector = _resolve_inspector_for_complaint(worker, commune)
        if inspector:
            vc.assigned_inspector = inspector
            vc.status = 'ASSIGNED'

        vc.save()

        # Lancer transcription Whisper + traduction GPT en arrière-plan
        from domestic.transcription_service import start_transcription_async
        start_transcription_async(vc.id)

        out = VoiceComplaintSerializer(vc, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        vc = self.get_object()
        if not is_admin_or_inspector(request.user):
            return Response({'detail': 'Accès réservé aux inspecteurs.'}, status=status.HTTP_403_FORBIDDEN)

        s = InspectorRespondSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        if 'response_text' in d and d['response_text']:
            vc.inspector_response_text = d['response_text']
        if 'response_audio' in d and d['response_audio']:
            vc.inspector_response_audio = d['response_audio']

        vc.status = 'RESPONDED'
        vc.save()
        return Response(VoiceComplaintSerializer(vc, context={'request': request}).data)

    @action(detail=False, methods=['get'], url_path='inspectors-in-unit')
    def inspectors_in_unit(self, request):
        """Liste des inspecteurs disponibles pour une assistance linguistique."""
        if not is_admin_or_inspector(request.user):
            return Response({'detail': 'Accès réservé aux inspecteurs.'}, status=status.HTTP_403_FORBIDDEN)
        from users.models import User as UserModel
        inspectors = UserModel.objects.filter(
            user_type__in=['INSPECTEUR', 'CHEF_INSPECTION'],
            is_active=True,
        ).exclude(id=request.user.id).order_by('first_name', 'last_name')
        return Response([{
            'id': i.id,
            'name': i.get_full_name(),
            'email': i.email,
            'user_type': i.user_type,
        } for i in inspectors])

    @action(detail=True, methods=['post'], url_path='request-assistance')
    def request_assistance(self, request, pk=None):
        vc = self.get_object()
        inspector_id = request.data.get('inspector_id')
        if not inspector_id:
            return Response({'detail': 'inspector_id requis.'}, status=status.HTTP_400_BAD_REQUEST)
        from users.models import User as UserModel
        try:
            assistant = UserModel.objects.get(
                id=inspector_id,
                user_type__in=['INSPECTEUR', 'CHEF_INSPECTION'],
                is_active=True,
            )
        except UserModel.DoesNotExist:
            return Response({'detail': 'Inspecteur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        vc.assistance_inspector = assistant
        vc.language_assistance_requested = True
        vc.status = 'ASSISTANCE_REQUESTED'
        vc.save()
        return Response(VoiceComplaintSerializer(vc, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='submit-assistance-note')
    def submit_assistance_note(self, request, pk=None):
        """L'inspecteur assistant soumet sa note d'interprétation."""
        vc = self.get_object()
        if vc.assistance_inspector_id != request.user.id:
            return Response(
                {'detail': "Action réservée à l'inspecteur assistant désigné."},
                status=status.HTTP_403_FORBIDDEN,
            )
        note = request.data.get('note', '').strip()
        if not note:
            return Response({'detail': 'La note ne peut pas être vide.'}, status=status.HTTP_400_BAD_REQUEST)
        vc.assistance_note = note
        vc.assistance_responded_at = timezone.now()
        vc.status = 'IN_PROGRESS'
        vc.save()
        return Response(VoiceComplaintSerializer(vc, context={'request': request}).data)


# ── Visites de terrain ────────────────────────────────────────────────────────

class FieldVisitViewSet(viewsets.ModelViewSet):
    serializer_class   = FieldVisitSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['status', 'commune', 'contract']

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'ADMIN':
            return FieldVisit.objects.all().select_related(
                'inspector', 'contract__worker__user', 'contract__employer__user'
            )
        if is_admin_or_inspector(user):
            return FieldVisit.objects.filter(inspector=user).select_related(
                'inspector', 'contract__worker__user', 'contract__employer__user'
            )
        return FieldVisit.objects.none()

    def perform_create(self, serializer):
        serializer.save(inspector=self.request.user)

    @action(detail=True, methods=['post'], url_path='record-gps')
    def record_gps(self, request, pk=None):
        """Enregistre la position GPS de l'inspecteur au moment de la visite."""
        visit = self.get_object()
        s = RecordGPSSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        visit.latitude  = d['latitude']
        visit.longitude = d['longitude']
        visit.address   = d.get('address', '')
        visit.status    = d['status']
        visit.actual_date = timezone.now()
        visit.save()
        return Response(FieldVisitSerializer(visit).data)

    @action(detail=False, methods=['get'], url_path='by-zone')
    def by_zone(self, request):
        """Retourne les visites regroupées par commune/zone."""
        user = request.user
        if not is_admin_or_inspector(user):
            return Response({'error': 'Accès réservé aux inspecteurs'}, status=status.HTTP_403_FORBIDDEN)

        qs = self.get_queryset()
        grouped: dict = {}
        for visit in qs:
            key = visit.commune or visit.zone_label or 'Non définie'
            grouped.setdefault(key, []).append(FieldVisitSerializer(visit).data)

        return Response([
            {'zone': k, 'count': len(v), 'visits': v}
            for k, v in sorted(grouped.items())
        ])
