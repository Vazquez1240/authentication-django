from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    username = serializers.CharField(write_only=True)
    uuid = serializers.CharField()

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password', 'uuid']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        if get_user_model().objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": ["Ya existe un usuario con ese correo electrónico."]})
        return data

    def create(self, validated_data):

        user = get_user_model().objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):

        token = super().get_token(user)

        token['is_superuser'] = user.is_superuser
        token['is_staff'] = user.is_staff
        token['user_id'] = user.id
        token['uuid'] = str(user.uuid)

        return token