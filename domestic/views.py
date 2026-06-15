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
from core.permissions import IsInspecteur, IsInspecteurOrEmploye, IsInspecteurOrEmployeur
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


def _best_inspector_from_zone(zone):
    """HEAD actif de la zone, sinon premier MEMBER, sinon head_inspector legacy."""
    from inspections.models import InspectorZoneAssignment
    head = InspectorZoneAssignment.objects.filter(
        zone=zone, role='HEAD', is_active=True, inspector__is_active=True
    ).select_related('inspector').first()
    if head:
        return head.inspector
    member = InspectorZoneAssignment.objects.filter(
        zone=zone, role='MEMBER', is_active=True, inspector__is_active=True
    ).select_related('inspector').first()
    if member:
        return member.inspector
    if zone.head_inspector and zone.head_inspector.is_active:
        return zone.head_inspector
    return None


def _find_inspector_for_city(city: str):
    """
    Trouve l'inspecteur le plus compétent pour une ville/commune donnée.
    Retourne l'inspecteur ou None (l'appelant gère le fallback ultime).
    """
    result, _ = _find_inspector_with_reason(city)
    return result


def _find_inspector_with_reason(city: str):
    """
    Même logique que _find_inspector_for_city, mais retourne aussi
    la raison de correspondance (pour affichage dans le dashboard admin).

    Retourne: (inspector | None, reason_str | None)
    """
    if not city:
        return None, None

    from inspections.models import Commune, InspectionZone

    # 1. Commune.name correspond
    commune = Commune.objects.filter(
        name__icontains=city, is_active=True, zone__isnull=False
    ).select_related('zone').first()
    if commune and commune.zone:
        inspector = _best_inspector_from_zone(commune.zone)
        if inspector:
            return inspector, f'Commune {commune.name} → {commune.zone.name}'

    # 2. Commune.city correspond (ville du bureau)
    commune_by_city = Commune.objects.filter(
        city__icontains=city, is_active=True, zone__isnull=False
    ).select_related('zone').first()
    if commune_by_city and commune_by_city.zone:
        inspector = _best_inspector_from_zone(commune_by_city.zone)
        if inspector:
            return inspector, f'Ville {city} → {commune_by_city.zone.name}'

    # 3. Zone.city correspond (ancien mécanisme)
    zone = InspectionZone.objects.filter(city__icontains=city, is_active=True).first()
    if zone:
        inspector = _best_inspector_from_zone(zone)
        if inspector:
            return inspector, f'Zone {zone.name}'

    return None, None


def _auto_assign_inspector(contract: DomesticContract) -> None:
    """
    Affecte l'inspecteur compétent à un contrat qui devient ACTIVE.

    Ordre de priorité :
      1. Inspecteur déjà assigné au worker (worker.assigned_inspector)
      2. Commune de résidence de l'employé (worker.user.city)
         → Commune → InspectionZone → InspectorZoneAssignment HEAD puis MEMBER
      3. Commune de l'employeur (employer.city) — lieu de travail
      4. Fallback ultime : premier INSPECTEUR actif en base

    Effet secondaire : propage l'inspecteur sur worker.assigned_inspector
    si celui-ci n'en a pas encore.
    """
    if contract.inspector:
        return  # déjà assigné

    from users.models import User as UserModel

    # 1. Inspecteur déjà assigné au worker directement
    if contract.worker.assigned_inspector and contract.worker.assigned_inspector.is_active:
        contract.inspector = contract.worker.assigned_inspector
        return

    # 2. Ville de résidence de l'employé
    worker_city = getattr(contract.worker.user, 'city', '') or ''
    inspector = _find_inspector_for_city(worker_city)

    # 3. Ville de l'employeur (lieu de travail)
    if not inspector:
        try:
            employer_city = getattr(contract.employer.user, 'city', '') or ''
            if not employer_city:
                employer_city = getattr(contract.employer, 'city', '') or ''
        except Exception:
            employer_city = ''
        if employer_city and employer_city != worker_city:
            inspector = _find_inspector_for_city(employer_city)

    # 4. Fallback ultime
    if not inspector:
        inspector = UserModel.objects.filter(
            user_type__in=['INSPECTEUR', 'CHEF_INSPECTION'], is_active=True
        ).first()

    if inspector:
        contract.inspector = inspector
        # Propager aussi sur le worker si pas encore assigné
        if not contract.worker.assigned_inspector:
            contract.worker.assigned_inspector = inspector
            contract.worker.save(update_fields=['assigned_inspector'])


def _resolve_inspector_for_complaint(worker, commune: str):
    """
    Retourne l'inspecteur à affecter à une plainte vocale.

    Ordre de priorité :
      1. Inspecteur directement assigné au worker
      2. Inspecteur du contrat actif
      3. Commune de la plainte → InspectionZone → InspectorZoneAssignment HEAD/MEMBER
      4. Ville de résidence du worker → même chaîne
      5. Fallback ultime : premier INSPECTEUR actif
    """
    from users.models import User as UserModel

    # 1. Inspecteur directement assigné au worker (sans contrat requis)
    if worker.assigned_inspector and worker.assigned_inspector.is_active:
        return worker.assigned_inspector

    # 2. Inspecteur du contrat actif
    active_contract = worker.contracts.filter(status='ACTIVE').select_related('inspector').first()
    if active_contract and active_contract.inspector and active_contract.inspector.is_active:
        return active_contract.inspector

    # 2. Commune déclarée dans la plainte
    inspector = _find_inspector_for_city(commune or '')
    if inspector:
        return inspector

    # 3. Ville de résidence du worker
    worker_city = getattr(worker.user, 'city', '') or ''
    if worker_city and worker_city != (commune or ''):
        inspector = _find_inspector_for_city(worker_city)
        if inspector:
            return inspector

    # 4. Fallback
    return UserModel.objects.filter(
        user_type__in=['INSPECTEUR', 'CHEF_INSPECTION'], is_active=True
    ).first()


# ── Workers ───────────────────────────────────────────────────────────────────

class DomesticWorkerViewSet(viewsets.ModelViewSet):
    serializer_class = DomesticWorkerSerializer
    permission_classes = [IsInspecteurOrEmploye]
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

    # ── Affectation inspecteur (sans contrat requis) ──────────────────────────

    @action(detail=False, methods=['get'], url_path='unassigned')
    def unassigned(self, request):
        """
        Liste des employés de maison sans inspecteur assigné,
        enrichis de la suggestion automatique.
        """
        if not is_admin_or_inspector(request.user):
            return Response({'detail': 'Accès réservé.'}, status=status.HTTP_403_FORBIDDEN)

        workers = DomesticWorker.objects.filter(
            assigned_inspector__isnull=True
        ).select_related('user', 'assigned_inspector').prefetch_related('contracts')

        data = DomesticWorkerSerializer(workers, many=True).data

        for worker_obj, worker_data in zip(workers, data):
            city = getattr(worker_obj.user, 'city', '') or ''
            inspector, reason = _find_inspector_with_reason(city)
            worker_data['suggested_inspector'] = {
                'inspector_id':    inspector.id,
                'inspector_name':  inspector.get_full_name(),
                'inspector_email': inspector.email,
                'match_reason':    reason,
            } if inspector else None

        return Response(data)

    @action(detail=True, methods=['get'], url_path='suggest-inspector')
    def suggest_inspector(self, request, pk=None):
        """Retourne l'inspecteur suggéré pour ce worker (sans l'affecter)."""
        if not is_admin_or_inspector(request.user):
            return Response({'detail': 'Accès réservé.'}, status=status.HTTP_403_FORBIDDEN)
        worker = self.get_object()
        city = getattr(worker.user, 'city', '') or ''
        inspector, reason = _find_inspector_with_reason(city)
        if not inspector:
            from users.models import User as UserModel
            inspector = UserModel.objects.filter(
                user_type__in=['INSPECTEUR', 'CHEF_INSPECTION'], is_active=True
            ).first()
            reason = 'Fallback — premier inspecteur disponible' if inspector else None
        if not inspector:
            return Response({'suggestion': None})
        return Response({'suggestion': {
            'inspector_id':    inspector.id,
            'inspector_name':  inspector.get_full_name(),
            'inspector_email': inspector.email,
            'match_reason':    reason,
        }})

    @action(detail=True, methods=['post'], url_path='assign-inspector')
    def assign_inspector(self, request, pk=None):
        """
        Affecte un inspecteur à un employé de maison.
        Met également à jour tous ses contrats actifs.
        """
        if not is_admin_or_inspector(request.user):
            return Response({'detail': 'Accès réservé.'}, status=status.HTTP_403_FORBIDDEN)
        worker = self.get_object()
        inspector_id = request.data.get('inspector_id')
        if not inspector_id:
            return Response({'detail': 'inspector_id requis.'}, status=status.HTTP_400_BAD_REQUEST)
        from users.models import User as UserModel
        try:
            inspector = UserModel.objects.get(
                id=inspector_id, user_type__in=['INSPECTEUR', 'CHEF_INSPECTION'], is_active=True
            )
        except UserModel.DoesNotExist:
            return Response({'detail': 'Inspecteur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        worker.assigned_inspector = inspector
        worker.save(update_fields=['assigned_inspector'])

        # Propager sur les contrats actifs sans inspecteur
        updated_contracts = worker.contracts.filter(
            status='ACTIVE', inspector__isnull=True
        ).update(inspector=inspector)

        return Response({
            'message': f'Inspecteur {inspector.get_full_name()} assigné.',
            'inspector_id':   inspector.id,
            'inspector_name': inspector.get_full_name(),
            'contracts_updated': updated_contracts,
        })

    @action(detail=False, methods=['post'], url_path='bulk-auto-assign')
    def bulk_auto_assign(self, request):
        """
        Affecte automatiquement tous les employés de maison sans inspecteur
        en utilisant la chaîne Commune → Zone → InspectorZoneAssignment.
        """
        if not is_admin_or_inspector(request.user):
            return Response({'detail': 'Accès réservé.'}, status=status.HTTP_403_FORBIDDEN)
        from users.models import User as UserModel

        workers = DomesticWorker.objects.filter(
            assigned_inspector__isnull=True
        ).select_related('user')

        assigned_count   = 0
        unresolved_ids   = []

        for worker in workers:
            city = getattr(worker.user, 'city', '') or ''
            inspector = _find_inspector_for_city(city)
            if not inspector:
                inspector = UserModel.objects.filter(
                    user_type__in=['INSPECTEUR', 'CHEF_INSPECTION'], is_active=True
                ).first()
            if inspector:
                worker.assigned_inspector = inspector
                worker.save(update_fields=['assigned_inspector'])
                # Propager sur les contrats actifs sans inspecteur
                worker.contracts.filter(status='ACTIVE', inspector__isnull=True).update(inspector=inspector)
                assigned_count += 1
            else:
                unresolved_ids.append(worker.id)

        return Response({
            'assigned':   assigned_count,
            'unresolved': len(unresolved_ids),
            'message': (
                f'{assigned_count} employé(s) affecté(s) automatiquement.'
                + (f' {len(unresolved_ids)} sans correspondance.' if unresolved_ids else '')
            ),
        })


# ── Employers ─────────────────────────────────────────────────────────────────

class DomesticEmployerViewSet(viewsets.ModelViewSet):
    serializer_class = DomesticEmployerSerializer
    permission_classes = [IsInspecteurOrEmployeur]

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
    permission_classes = [IsInspecteurOrEmployeur]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'worker', 'employer']

    def perform_create(self, serializer):
        """
        Auto-assigne l'employeur si connecté en tant qu'EMPLOYEUR.
        Hérite de l'inspecteur du worker si déjà assigné (sans contrat requis).
        """
        extra = {}
        if self.request.user.user_type == 'EMPLOYEUR':
            extra['employer'] = DomesticEmployer.objects.get(user=self.request.user)

        contract = serializer.save(**extra)

        # Hériter l'inspecteur du worker si disponible
        if not contract.inspector:
            worker_id = contract.worker_id
            try:
                worker = DomesticWorker.objects.select_related('assigned_inspector').get(id=worker_id)
                if worker.assigned_inspector and worker.assigned_inspector.is_active:
                    contract.inspector = worker.assigned_inspector
                    contract.save(update_fields=['inspector'])
            except DomesticWorker.DoesNotExist:
                pass

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

    @action(detail=True, methods=['get'], url_path='suggest-inspector')
    def suggest_inspector(self, request, pk=None):
        """
        Retourne l'inspecteur suggéré pour un contrat (sans l'affecter).
        Utile pour afficher une suggestion dans le dashboard admin.
        """
        if request.user.user_type not in ('ADMIN', 'CHEF_INSPECTION', 'DIRECTEUR_REGIONAL', 'DIRECTEUR_GENERAL'):
            return Response({'detail': 'Accès réservé.'}, status=status.HTTP_403_FORBIDDEN)
        contract = self.get_object()

        worker_city = getattr(contract.worker.user, 'city', '') or ''
        inspector, reason = _find_inspector_with_reason(worker_city)

        if not inspector:
            try:
                employer_city = getattr(contract.employer.user, 'city', '') or getattr(contract.employer, 'city', '') or ''
            except Exception:
                employer_city = ''
            if employer_city and employer_city != worker_city:
                inspector, reason = _find_inspector_with_reason(employer_city)
                if inspector and reason:
                    reason = f'{reason} (lieu de travail)'

        if not inspector:
            from users.models import User as UserModel
            inspector = UserModel.objects.filter(
                user_type__in=['INSPECTEUR', 'CHEF_INSPECTION'], is_active=True
            ).first()
            reason = 'Fallback — premier inspecteur disponible' if inspector else None

        if not inspector:
            return Response({'suggestion': None})

        return Response({
            'suggestion': {
                'inspector_id':   inspector.id,
                'inspector_name': inspector.get_full_name(),
                'inspector_email': inspector.email,
                'match_reason':   reason,
            }
        })

    @action(detail=False, methods=['post'], url_path='bulk-auto-assign')
    def bulk_auto_assign(self, request):
        """
        Affecte automatiquement tous les contrats actifs sans inspecteur
        en utilisant la chaîne Commune → Zone → InspectorZoneAssignment.
        Retourne le nombre de contrats affectés et ceux sans correspondance.
        """
        if request.user.user_type not in ('ADMIN', 'CHEF_INSPECTION', 'DIRECTEUR_REGIONAL', 'DIRECTEUR_GENERAL'):
            return Response({'detail': 'Accès réservé.'}, status=status.HTTP_403_FORBIDDEN)

        contracts = DomesticContract.objects.filter(
            status='ACTIVE', inspector__isnull=True
        ).select_related('worker__user', 'employer__user', 'employer')

        assigned_count   = 0
        unresolved_ids   = []

        for contract in contracts:
            _auto_assign_inspector(contract)
            if contract.inspector:
                contract.save(update_fields=['inspector'])
                assigned_count += 1
            else:
                unresolved_ids.append(contract.id)

        return Response({
            'assigned':   assigned_count,
            'unresolved': len(unresolved_ids),
            'unresolved_contract_ids': unresolved_ids,
            'message': (
                f'{assigned_count} contrat(s) affecté(s) automatiquement.'
                + (f' {len(unresolved_ids)} contrat(s) sans inspecteur trouvé.' if unresolved_ids else '')
            ),
        })

    @action(detail=False, methods=['get'], url_path='unassigned')
    def unassigned(self, request):
        """
        Liste des contrats actifs sans inspecteur, enrichis de la suggestion
        automatique (inspector suggéré + raison de correspondance).
        """
        if request.user.user_type not in ('ADMIN', 'CHEF_INSPECTION', 'DIRECTEUR_REGIONAL', 'DIRECTEUR_GENERAL'):
            return Response({'detail': 'Accès réservé.'}, status=status.HTTP_403_FORBIDDEN)

        contracts = DomesticContract.objects.filter(
            status='ACTIVE', inspector__isnull=True
        ).select_related('worker__user', 'employer__user', 'employer')

        data = DomesticContractSerializer(contracts, many=True).data

        # Enrichit chaque contrat avec la suggestion automatique
        for contract_obj, contract_data in zip(contracts, data):
            worker_city = getattr(contract_obj.worker.user, 'city', '') or ''
            inspector, reason = _find_inspector_with_reason(worker_city)

            if not inspector:
                try:
                    employer_city = (
                        getattr(contract_obj.employer.user, 'city', '')
                        or getattr(contract_obj.employer, 'city', '') or ''
                    )
                except Exception:
                    employer_city = ''
                if employer_city and employer_city != worker_city:
                    inspector, reason = _find_inspector_with_reason(employer_city)
                    if inspector and reason:
                        reason = f'{reason} (lieu de travail)'

            if inspector:
                contract_data['suggested_inspector'] = {
                    'inspector_id':    inspector.id,
                    'inspector_name':  inspector.get_full_name(),
                    'inspector_email': inspector.email,
                    'match_reason':    reason,
                }
            else:
                contract_data['suggested_inspector'] = None

        return Response(data)


# ── Time Tracking (Pointage) ──────────────────────────────────────────────────

class TimeTrackingViewSet(viewsets.ModelViewSet):
    serializer_class = TimeTrackingSerializer
    permission_classes = [IsInspecteurOrEmploye]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contract', 'worker', 'date', 'is_validated']

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        if is_admin_or_inspector(user):
            return TimeTracking.objects.all()
        if user.user_type in ('EMPLOYE', 'EMPLOYE_MAISON'):
            worker_ids = DomesticWorker.objects.filter(user=user).values_list('id', flat=True)
            return TimeTracking.objects.filter(
                Q(worker_id__in=worker_ids) | Q(contract__worker_id__in=worker_ids)
            ).distinct()
        if user.user_type == 'EMPLOYEUR':
            employer_ids = DomesticEmployer.objects.filter(user=user).values_list('id', flat=True)
            return TimeTracking.objects.filter(contract__employer_id__in=employer_ids)
        return TimeTracking.objects.none()

    @action(detail=False, methods=['post'])
    def checkin(self, request):
        """
        Pointer l'arrivée. Accepte contract_id OU worker_id (contrat facultatif).
        Géofencing activé seulement si un contrat avec adresse employeur est fourni.
        """
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contract_id = serializer.validated_data.get('contract_id')
        worker_id   = serializer.validated_data.get('worker_id')

        contract = None
        worker   = None

        if contract_id:
            try:
                contract = DomesticContract.objects.select_related('worker', 'employer').get(id=contract_id)
                worker   = contract.worker
            except DomesticContract.DoesNotExist:
                return Response({'error': 'Contrat introuvable'}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                if worker_id:
                    worker = DomesticWorker.objects.get(id=worker_id)
                else:
                    worker = DomesticWorker.objects.get(user=request.user)
            except DomesticWorker.DoesNotExist:
                return Response({'error': 'Employé introuvable'}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()

        # RG-DOM-003 : géofencing (seulement quand l'employeur a des coordonnées)
        if contract:
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

        # Vérification doublon du jour
        from django.db.models import Q
        existing = TimeTracking.objects.filter(
            Q(worker=worker) | (Q(contract=contract) if contract else Q()),
            date=today,
        ).first()
        if existing:
            return Response(
                {'error': "Pointage déjà effectué aujourd'hui"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tracking = TimeTracking.objects.create(
            worker=worker,
            contract=contract,
            date=today,
            check_in_time=timezone.now(),
            check_in_latitude=serializer.validated_data['latitude'],
            check_in_longitude=serializer.validated_data['longitude'],
            check_in_address=serializer.validated_data.get('address', ''),
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
        worker_id   = request.query_params.get('worker_id')
        month       = request.query_params.get('month')

        if not month:
            return Response({'error': 'month requis'}, status=status.HTTP_400_BAD_REQUEST)
        if not contract_id and not worker_id:
            return Response({'error': 'contract_id ou worker_id requis'}, status=status.HTTP_400_BAD_REQUEST)

        month_date = datetime.strptime(month, '%Y-%m-%d').date()
        first_day  = month_date.replace(day=1)
        last_day   = (first_day + relativedelta(months=1)) - relativedelta(days=1)

        from django.db.models import Q
        if contract_id:
            trackings = TimeTracking.objects.filter(
                Q(contract_id=contract_id) | Q(worker=DomesticContract.objects.filter(id=contract_id).values('worker').first()['worker'] if DomesticContract.objects.filter(id=contract_id).exists() else None),
                date__gte=first_day, date__lte=last_day,
            ).distinct()
        else:
            trackings = TimeTracking.objects.filter(
                Q(worker_id=worker_id) | Q(contract__worker_id=worker_id),
                date__gte=first_day, date__lte=last_day,
            ).distinct()

        total_hours    = sum([t.hours_worked for t in trackings], Decimal('0'))
        total_overtime = sum([t.overtime_hours for t in trackings], Decimal('0'))

        return Response({
            'month':         month,
            'total_days':    trackings.count(),
            'total_hours':   float(total_hours),
            'total_overtime': float(total_overtime),
            'trackings':     TimeTrackingSerializer(trackings, many=True).data,
        })

    @action(detail=False, methods=['get'])
    def abuse_alerts(self, request):
        """
        Détection automatique d'abus (RG-DOM-005).
        Analyse les 30 derniers jours. Accepte contract_id ou worker_id.
        """
        contract_id = request.query_params.get('contract_id')
        worker_id   = request.query_params.get('worker_id')

        if not contract_id and not worker_id:
            return Response({'error': 'contract_id ou worker_id requis'}, status=status.HTTP_400_BAD_REQUEST)

        contract = None
        worker   = None

        if contract_id:
            try:
                contract = DomesticContract.objects.select_related('worker').get(id=contract_id)
                worker   = contract.worker
            except DomesticContract.DoesNotExist:
                return Response({'error': 'Contrat introuvable'}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                worker = DomesticWorker.objects.get(id=worker_id)
            except DomesticWorker.DoesNotExist:
                return Response({'error': 'Employé introuvable'}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()
        since = today - timedelta(days=30)
        from django.db.models import Q
        trackings = list(TimeTracking.objects.filter(
            Q(worker=worker) | (Q(contract=contract) if contract else Q()),
            date__gte=since, date__lte=today,
        ).distinct())

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

        # Salaire inférieur au SMIG (seulement si contrat disponible)
        if contract and contract.salary and contract.salary < SMIG_CI_MONTHLY:
            alerts.append({
                'type': 'BELOW_MINIMUM_WAGE',
                'severity': 'CRITICAL',
                'message': (
                    f'Salaire ({float(contract.salary):,.0f} FCFA) inférieur au SMIG '
                    f'({float(SMIG_CI_MONTHLY):,.0f} FCFA/mois)'
                ),
            })

        return Response({
            'contract_id': int(contract_id) if contract_id else None,
            'worker_id':   worker.id,
            'period':      {'from': str(since), 'to': str(today)},
            'alert_count': len(alerts),
            'alerts':      alerts,
        })

    @action(detail=False, methods=['get'], url_path='address-book')
    def address_book(self, request):
        """
        Carnet d'adresses : employés avec contrat actif + employés sans contrat
        mais avec assigned_inspector. Groupé par commune / zone géographique.
        """
        user = request.user
        if not is_admin_or_inspector(user):
            return Response({'error': 'Accès réservé aux inspecteurs'}, status=status.HTTP_403_FORBIDDEN)

        from django.db.models import Q
        from inspections.models import InspectionZone

        def _zone_for_commune(commune):
            if not commune:
                return ''
            zone = InspectionZone.objects.filter(city__icontains=commune, is_active=True).first()
            return zone.name if zone else ''

        def _entry_from_tracking(worker, contract, latest, total):
            commune = ''
            if latest and latest.check_in_address:
                parts = [p.strip() for p in latest.check_in_address.split(',')]
                commune = parts[-1] if parts else ''
            if not commune:
                commune = (contract.employer.city if contract else '') or getattr(worker.user, 'city', '') or ''
            return {
                'worker_id':              worker.id,
                'worker_name':            worker.user.get_full_name(),
                'specialization':         worker.specialization,
                'specialization_display': worker.get_specialization_display(),
                'contract_id':            contract.id if contract else None,
                'employer_name':          contract.employer.user.get_full_name() if contract else None,
                'employer_address':       contract.employer.address if contract else '',
                'commune':                commune,
                'zone_name':              _zone_for_commune(commune),
                'last_checkin_date':      latest.date.isoformat() if latest else None,
                'last_checkin_time':      latest.check_in_time.isoformat() if latest else None,
                'last_address':           latest.check_in_address if latest else '',
                'latitude':               float(latest.check_in_latitude)  if latest and latest.check_in_latitude  else None,
                'longitude':              float(latest.check_in_longitude) if latest and latest.check_in_longitude else None,
                'total_checkins':         total,
            }

        result      = []
        seen_worker = set()

        # 1. Workers avec contrat actif
        if user.user_type == 'ADMIN':
            contracts = DomesticContract.objects.filter(status='ACTIVE').select_related('worker__user', 'employer', 'inspector')
        else:
            contracts = DomesticContract.objects.filter(inspector=user, status='ACTIVE').select_related('worker__user', 'employer')

        for contract in contracts:
            worker = contract.worker
            seen_worker.add(worker.id)
            latest = TimeTracking.objects.filter(
                Q(worker=worker) | Q(contract=contract)
            ).order_by('-check_in_time').first()
            total = TimeTracking.objects.filter(Q(worker=worker) | Q(contract=contract)).distinct().count()
            result.append(_entry_from_tracking(worker, contract, latest, total))

        # 2. Workers sans contrat actif mais avec assigned_inspector
        if user.user_type == 'ADMIN':
            direct_workers = DomesticWorker.objects.filter(
                assigned_inspector__isnull=False
            ).exclude(id__in=seen_worker).select_related('user', 'assigned_inspector')
        else:
            direct_workers = DomesticWorker.objects.filter(
                assigned_inspector=user
            ).exclude(id__in=seen_worker).select_related('user')

        for worker in direct_workers:
            latest = TimeTracking.objects.filter(worker=worker).order_by('-check_in_time').first()
            total  = TimeTracking.objects.filter(worker=worker).count()
            result.append(_entry_from_tracking(worker, None, latest, total))

        result.sort(key=lambda x: (x['commune'] or 'zzz', x['worker_name']))
        return Response(result)


# ── Payslips ──────────────────────────────────────────────────────────────────

class MonthlyPayslipViewSet(viewsets.ModelViewSet):
    serializer_class = MonthlyPayslipSerializer
    permission_classes = [IsInspecteur]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contract', 'worker', 'status', 'month']

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        if is_admin_or_inspector(user):
            return MonthlyPayslip.objects.all()
        if user.user_type in ('EMPLOYE', 'EMPLOYE_MAISON'):
            worker_ids = DomesticWorker.objects.filter(user=user).values_list('id', flat=True)
            return MonthlyPayslip.objects.filter(
                Q(worker_id__in=worker_ids) | Q(contract__worker_id__in=worker_ids)
            ).distinct()
        if user.user_type == 'EMPLOYEUR':
            employer_ids = DomesticEmployer.objects.filter(user=user).values_list('id', flat=True)
            return MonthlyPayslip.objects.filter(contract__employer_id__in=employer_ids)
        return MonthlyPayslip.objects.none()

    @action(detail=False, methods=['post'])
    def generate(self, request):
        serializer = GeneratePayslipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contract_id = serializer.validated_data.get('contract_id')
        worker_id   = serializer.validated_data.get('worker_id')

        contract = None
        worker   = None

        if contract_id:
            try:
                contract = DomesticContract.objects.select_related('worker').get(id=contract_id)
                worker   = contract.worker
            except DomesticContract.DoesNotExist:
                return Response({'error': 'Contrat introuvable'}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                worker = DomesticWorker.objects.get(id=worker_id)
            except DomesticWorker.DoesNotExist:
                return Response({'error': 'Employé introuvable'}, status=status.HTTP_404_NOT_FOUND)

        month_date = serializer.validated_data['month']
        first_day  = month_date.replace(day=1)
        last_day   = (first_day + relativedelta(months=1)) - relativedelta(days=1)

        from django.db.models import Q
        if contract:
            trackings = TimeTracking.objects.filter(
                Q(contract=contract) | Q(worker=worker),
                date__gte=first_day, date__lte=last_day, is_validated=True,
            ).distinct()
        else:
            trackings = TimeTracking.objects.filter(
                Q(worker=worker) | Q(contract__worker=worker),
                date__gte=first_day, date__lte=last_day, is_validated=True,
            ).distinct()

        regular_hours  = sum([t.hours_worked - t.overtime_hours for t in trackings], Decimal('0'))
        overtime_hours = sum([t.overtime_hours for t in trackings], Decimal('0'))

        if contract:
            base_salary         = contract.salary
            transport_allowance = contract.transportation_allowance
        else:
            base_salary         = serializer.validated_data.get('base_salary') or Decimal('0')
            transport_allowance = Decimal('0')

        hourly_rate   = base_salary / Decimal('160') if base_salary else Decimal('0')
        overtime_rate = hourly_rate * Decimal('1.5')

        if contract:
            payslip, created = MonthlyPayslip.objects.get_or_create(
                contract=contract, worker=worker, month=first_day,
                defaults={
                    'base_salary':            base_salary,
                    'transportation_allowance': transport_allowance,
                    'status':            'DRAFT',
                    'gross_pay':         base_salary,
                    'total_deductions':  Decimal('0'),
                    'net_pay':           base_salary,
                },
            )
        else:
            payslip, created = MonthlyPayslip.objects.get_or_create(
                worker=worker, contract=None, month=first_day,
                defaults={
                    'base_salary':            base_salary,
                    'transportation_allowance': transport_allowance,
                    'status':            'DRAFT',
                    'gross_pay':         base_salary,
                    'total_deductions':  Decimal('0'),
                    'net_pay':           base_salary,
                },
            )

        payslip.regular_hours  = regular_hours
        payslip.overtime_hours = overtime_hours
        payslip.overtime_pay   = overtime_hours * overtime_rate
        payslip.bonuses          = serializer.validated_data.get('bonuses', Decimal('0'))
        payslip.other_deductions = serializer.validated_data.get('other_deductions', Decimal('0'))
        payslip.social_security  = (payslip.base_salary + payslip.overtime_pay) * Decimal('0.025')
        payslip.calculate_totals()
        payslip.status = 'GENERATED'

        return Response({
            'message': 'Bulletin généré',
            'payslip': MonthlyPayslipSerializer(payslip).data,
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
    permission_classes = [IsInspecteurOrEmploye]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contract', 'worker', 'status', 'leave_type']

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        if is_admin_or_inspector(user):
            return LeaveRequest.objects.all()
        if user.user_type in ('EMPLOYE', 'EMPLOYE_MAISON'):
            worker_ids = DomesticWorker.objects.filter(user=user).values_list('id', flat=True)
            return LeaveRequest.objects.filter(
                Q(worker_id__in=worker_ids) | Q(contract__worker_id__in=worker_ids)
            ).distinct()
        if user.user_type == 'EMPLOYEUR':
            employer_ids = DomesticEmployer.objects.filter(user=user).values_list('id', flat=True)
            return LeaveRequest.objects.filter(contract__employer_id__in=employer_ids)
        return LeaveRequest.objects.none()

    def perform_create(self, serializer):
        """Auto-renseigne le worker depuis le contrat ou l'utilisateur connecté."""
        contract = serializer.validated_data.get('contract')
        worker   = serializer.validated_data.get('worker')
        if not worker and not contract:
            try:
                worker = DomesticWorker.objects.get(user=self.request.user)
            except DomesticWorker.DoesNotExist:
                pass
        if contract and not worker:
            worker = contract.worker
        serializer.save(worker=worker)

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
    permission_classes = [IsInspecteurOrEmploye]

    def _get_today_tracking(self, user):
        """
        Retourne (worker, tracking, error).
        Ne nécessite plus de contrat actif : cherche par worker directement.
        """
        try:
            worker = DomesticWorker.objects.get(user=user)
        except DomesticWorker.DoesNotExist:
            return None, None, 'Profil introuvable.'

        today    = timezone.now().date()
        from django.db.models import Q
        tracking = TimeTracking.objects.filter(
            Q(worker=worker) | Q(contract__worker=worker),
            date=today,
        ).first()

        if not tracking:
            return None, None, "Aucun pointage d'arrivée aujourd'hui."
        return worker, tracking, None

    def list(self, request):
        _, tracking, err = self._get_today_tracking(request.user)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        date_str = request.query_params.get('date')
        if date_str:
            try:
                from datetime import date as date_cls
                from django.db.models import Q
                d      = date_cls.fromisoformat(date_str)
                worker = DomesticWorker.objects.get(user=request.user)
                tracking = TimeTracking.objects.filter(
                    Q(worker=worker) | Q(contract__worker=worker), date=d
                ).first()
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
    permission_classes = [IsInspecteurOrEmploye]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        if is_admin_or_inspector(user):
            if user.user_type == 'INSPECTEUR':
                # Assignées à cet inspecteur + non encore assignées (à prendre en charge)
                return VoiceComplaint.objects.filter(
                    Q(assigned_inspector=user) |
                    Q(assistance_inspector=user) |
                    Q(assigned_inspector__isnull=True)
                )
            # CHEF_INSPECTION, DIRECTEUR, ADMIN → tout voir
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
    permission_classes = [IsInspecteur]
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['status', 'commune', 'contract', 'worker']

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'ADMIN':
            return FieldVisit.objects.all().select_related(
                'inspector',
                'worker__user',
                'contract__worker__user', 'contract__employer__user',
            )
        if is_admin_or_inspector(user):
            return FieldVisit.objects.filter(inspector=user).select_related(
                'inspector',
                'worker__user',
                'contract__worker__user', 'contract__employer__user',
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
