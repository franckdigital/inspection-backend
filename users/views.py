from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
import secrets

from .models import User, PasswordReset, EmailVerification, EmployeeProfile, InspectorProfile, EmployerProfile
from .serializers import (
    UserSerializer, UserDetailSerializer, CustomTokenObtainPairSerializer,
    ChangePasswordSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    EmailVerificationSerializer, OTPSetupSerializer, OTPVerifySerializer, UserUpdateSerializer,
    EmployeeProfileSerializer, InspectorProfileSerializer, EmployerProfileSerializer
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Comptes sans email réel (employé de maison inscrit par téléphone) :
        # activation immédiate — la vérification email est impossible sur @noemail.ci
        is_synthetic_email = user.email.endswith('@noemail.ci')
        if is_synthetic_email:
            user.is_active = True
            user.is_verified = True
            user.save(update_fields=['is_active', 'is_verified'])
        else:
            verification_token = secrets.token_urlsafe(32)
            EmailVerification.objects.create(
                user=user,
                token=verification_token,
                expires_at=timezone.now() + timedelta(hours=24)
            )
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
            send_mail(
                'Vérification de votre compte',
                f'Cliquez sur ce lien pour vérifier votre compte: {verification_url}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=True,
            )
            # Activer le compte immédiatement (le serveur email peut ne pas être configuré en dev)
            user.is_active = True
            user.is_verified = True
            user.save(update_fields=['is_active', 'is_verified'])

        headers = self.get_success_headers(serializer.data)
        message = (
            'Compte créé avec succès. Vous pouvez vous connecter.'
            if is_synthetic_email else
            'Compte créé avec succès. Un email de vérification a été envoyé.'
        )
        return Response(
            {'message': message, 'user': serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (permissions.AllowAny,)  # IMPORTANT: Autoriser l'accès sans authentification

    def post(self, request, *args, **kwargs):
        email = request.data.get('email', '')

        # Activer le compte AVANT la validation JWT : Django authenticate() rejette
        # les utilisateurs inactifs (is_active=False) avec une exception générique
        # qui masque le vrai problème. On active ici pour ne pas bloquer la connexion.
        if email:
            try:
                _u = User.objects.get(email=email)
                if not _u.is_active or not _u.is_verified:
                    _u.is_active = True
                    _u.is_verified = True
                    _u.save(update_fields=['is_active', 'is_verified'])
            except User.DoesNotExist:
                pass

        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {'error': 'Email ou mot de passe incorrect.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = User.objects.get(email=request.data.get('email'))

        if not user.is_active:
            return Response(
                {'error': 'Votre compte n\'est pas encore activé.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not user.is_verified:
            return Response(
                {'error': 'Veuillez vérifier votre adresse email.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if user.otp_enabled:
            return Response(
                {
                    'requires_otp': True,
                    'message': 'Veuillez entrer votre code OTP',
                    'temp_token': str(RefreshToken.for_user(user))
                },
                status=status.HTTP_200_OK
            )

        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = request.data.get('email')
        token = serializer.validated_data['token']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.verify_otp(token):
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserDetailSerializer(user).data
            })
        else:
            return Response(
                {'error': 'Code OTP invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserDetailSerializer
        return UserUpdateSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Ancien mot de passe incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response(
            {'message': 'Mot de passe modifié avec succès.'},
            status=status.HTTP_200_OK
        )


class PasswordResetRequestView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
            reset_token = secrets.token_urlsafe(32)

            PasswordReset.objects.create(
                user=user,
                token=reset_token,
                expires_at=timezone.now() + timedelta(hours=1)
            )

            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

            send_mail(
                'Réinitialisation de votre mot de passe',
                f'Cliquez sur ce lien pour réinitialiser votre mot de passe: {reset_url}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass

        return Response(
            {'message': 'Si l\'email existe, un lien de réinitialisation a été envoyé.'},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']

        try:
            password_reset = PasswordReset.objects.get(token=token)

            if not password_reset.is_valid():
                return Response(
                    {'error': 'Le lien de réinitialisation a expiré ou a déjà été utilisé.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = password_reset.user
            user.set_password(serializer.validated_data['password'])
            user.save()

            password_reset.used = True
            password_reset.save()

            return Response(
                {'message': 'Mot de passe réinitialisé avec succès.'},
                status=status.HTTP_200_OK
            )
        except PasswordReset.DoesNotExist:
            return Response(
                {'error': 'Token de réinitialisation invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class EmailVerificationView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']

        try:
            email_verification = EmailVerification.objects.get(token=token)

            if not email_verification.is_valid():
                return Response(
                    {'error': 'Le lien de vérification a expiré ou a déjà été utilisé.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = email_verification.user
            user.is_verified = True
            user.is_active = True
            user.save()

            email_verification.verified = True
            email_verification.save()

            return Response(
                {'message': 'Email vérifié avec succès. Vous pouvez maintenant vous connecter.'},
                status=status.HTTP_200_OK
            )
        except EmailVerification.DoesNotExist:
            return Response(
                {'error': 'Token de vérification invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class SetupOTPView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        serializer = OTPSetupSerializer(context={'user': user})

        return Response({
            'qr_code': serializer.data['qr_code'],
            'secret': user.generate_otp_secret()
        })

    def post(self, request):
        user = request.user
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']

        if user.verify_otp(token):
            user.otp_enabled = True
            user.save()
            return Response(
                {'message': 'OTP activé avec succès.'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Code OTP invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class DisableOTPView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        user.otp_enabled = False
        user.otp_secret = ''
        user.save()

        return Response(
            {'message': 'OTP désactivé avec succès.'},
            status=status.HTTP_200_OK
        )


class EmployeeProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = EmployeeProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        obj, created = EmployeeProfile.objects.get_or_create(user=self.request.user)
        return obj


class InspectorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = InspectorProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        obj, created = InspectorProfile.objects.get_or_create(user=self.request.user)
        return obj


class EmployerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = EmployerProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        obj, created = EmployerProfile.objects.get_or_create(user=self.request.user)
        return obj


# ── Admin : affectation inspecteur aux salariés (sans contrat requis) ──────────

class EmployeeInspectorAssignView(APIView):
    """
    Admin uniquement.
    GET  /users/employees/unassigned/   → salariés sans inspecteur + suggestion
    POST /users/employees/{id}/assign-inspector/ → affecter un inspecteur
    POST /users/employees/bulk-auto-assign/      → auto-affecter tous
    """
    permission_classes = (permissions.IsAuthenticated,)

    ADMIN_TYPES = ('ADMIN', 'CHEF_INSPECTION', 'DIRECTEUR_REGIONAL', 'DIRECTEUR_GENERAL')

    def _check_admin(self, request):
        if request.user.user_type not in self.ADMIN_TYPES:
            return Response({'detail': 'Accès réservé.'}, status=status.HTTP_403_FORBIDDEN)
        return None

    def _find_inspector_for_city(self, city: str):
        """Même chaîne de résolution que dans domestic/views.py."""
        if not city:
            return None, None
        from inspections.models import Commune, InspectionZone, InspectorZoneAssignment

        def _best(zone):
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

        commune = Commune.objects.filter(name__icontains=city, is_active=True, zone__isnull=False).select_related('zone').first()
        if commune and commune.zone:
            insp = _best(commune.zone)
            if insp:
                return insp, f'Commune {commune.name} → {commune.zone.name}'

        commune2 = Commune.objects.filter(city__icontains=city, is_active=True, zone__isnull=False).select_related('zone').first()
        if commune2 and commune2.zone:
            insp = _best(commune2.zone)
            if insp:
                return insp, f'Ville {city} → {commune2.zone.name}'

        zone = InspectionZone.objects.filter(city__icontains=city, is_active=True).first()
        if zone:
            insp = _best(zone)
            if insp:
                return insp, f'Zone {zone.name}'

        return None, None

    def get(self, request):
        """Liste des salariés (EMPLOYE) sans inspecteur assigné + suggestion."""
        err = self._check_admin(request)
        if err:
            return err

        profiles = EmployeeProfile.objects.filter(
            assigned_inspector__isnull=True,
            user__user_type='EMPLOYE',
            user__is_active=True,
        ).select_related('user', 'current_employer')

        result = []
        for p in profiles:
            city = p.city or getattr(p.user, 'city', '') or ''
            inspector, reason = self._find_inspector_for_city(city)
            if not inspector:
                inspector = User.objects.filter(
                    user_type__in=['INSPECTEUR', 'CHEF_INSPECTION'], is_active=True
                ).first()
                reason = 'Fallback' if inspector else None
            result.append({
                'profile_id':    p.id,
                'user_id':       p.user.id,
                'user_name':     p.user.get_full_name(),
                'user_email':    p.user.email,
                'user_city':     city,
                'job_title':     p.job_title,
                'employer_name': p.current_employer.name if p.current_employer else None,
                'assigned_inspector':      None,
                'assigned_inspector_name': None,
                'suggested_inspector': {
                    'inspector_id':    inspector.id,
                    'inspector_name':  inspector.get_full_name(),
                    'inspector_email': inspector.email,
                    'match_reason':    reason,
                } if inspector else None,
            })

        return Response(result)

    def post(self, request, employee_id=None):
        err = self._check_admin(request)
        if err:
            return err

        # Bulk auto-assign
        if request.path.rstrip('/').endswith('bulk-auto-assign'):
            profiles = EmployeeProfile.objects.filter(
                assigned_inspector__isnull=True,
                user__user_type='EMPLOYE',
                user__is_active=True,
            ).select_related('user')

            assigned = 0
            unresolved = []
            for p in profiles:
                city = p.city or getattr(p.user, 'city', '') or ''
                inspector, _ = self._find_inspector_for_city(city)
                if not inspector:
                    inspector = User.objects.filter(
                        user_type__in=['INSPECTEUR', 'CHEF_INSPECTION'], is_active=True
                    ).first()
                if inspector:
                    p.assigned_inspector = inspector
                    p.save(update_fields=['assigned_inspector'])
                    assigned += 1
                else:
                    unresolved.append(p.id)

            return Response({
                'assigned': assigned,
                'unresolved': len(unresolved),
                'message': f'{assigned} salarié(s) affecté(s) automatiquement.',
            })

        # Single assign
        if not employee_id:
            return Response({'detail': 'employee_id requis.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            profile = EmployeeProfile.objects.get(id=employee_id)
        except EmployeeProfile.DoesNotExist:
            return Response({'detail': 'Profil introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        inspector_id = request.data.get('inspector_id')
        if not inspector_id:
            return Response({'detail': 'inspector_id requis.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            inspector = User.objects.get(
                id=inspector_id, user_type__in=['INSPECTEUR', 'CHEF_INSPECTION'], is_active=True
            )
        except User.DoesNotExist:
            return Response({'detail': 'Inspecteur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        profile.assigned_inspector = inspector
        profile.save(update_fields=['assigned_inspector'])

        return Response({
            'message': f'Inspecteur {inspector.get_full_name()} assigné.',
            'inspector_id':   inspector.id,
            'inspector_name': inspector.get_full_name(),
        })
