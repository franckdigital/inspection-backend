from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, EmployeeProfile, InspectorProfile, EmployerProfile
import qrcode
import io
import base64


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'phone_number', 'first_name', 'last_name',
            'gender', 'date_of_birth', 'profile_picture', 'profile_picture_url',
            'user_type', 'is_active', 'is_verified', 'otp_enabled',
            'password', 'password2', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'is_active', 'is_verified', 'created_at', 'updated_at')

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return None

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'phone_number', 'first_name', 'last_name', 'full_name',
            'gender', 'date_of_birth', 'profile_picture', 'profile_picture_url',
            'user_type', 'is_active', 'is_verified', 'otp_enabled',
            'created_at', 'updated_at', 'last_login'
        )
        read_only_fields = fields

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
        return None

    def get_full_name(self, obj):
        return obj.get_full_name()


class EmployeeProfileSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = '__all__'


class InspectorProfileSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)

    class Meta:
        model = InspectorProfile
        fields = '__all__'


class EmployerProfileSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)

    class Meta:
        model = EmployerProfile
        fields = '__all__'


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add user information to response
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'user_type': self.user.user_type,
            'is_verified': self.user.is_verified,
            'otp_enabled': self.user.otp_enabled,
        }

        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Les nouveaux mots de passe ne correspondent pas."})
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    password = serializers.CharField(required=True, validators=[validate_password])
    password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)


class OTPSetupSerializer(serializers.Serializer):
    qr_code = serializers.SerializerMethodField()
    secret = serializers.CharField(read_only=True)

    def get_qr_code(self, obj):
        user = self.context.get('user')
        if not user:
            return None

        secret = user.generate_otp_secret()
        uri = user.get_otp_uri()

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"


class OTPVerifySerializer(serializers.Serializer):
    token = serializers.CharField(required=True, max_length=6, min_length=6)


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'phone_number',
            'gender', 'date_of_birth', 'profile_picture'
        )

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
