from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    username = serializers.CharField(write_only=True)
    uuid = serializers.CharField(read_only=True)
    rol_usuario = serializers.ChoiceField(choices=User.Roles.choices, default=User.Roles.USUARIO_NORMAL)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password', 'uuid', 'rol_usuario']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        if get_user_model().objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": ["Ya existe un usuario con ese correo electrónico."]})

        rol = data['rol_usuario']
        roles_validos = [r[0] for r in get_user_model().Roles.choices]
        if rol not in roles_validos:
            raise serializers.ValidationError({
                "rol_usuario": [f"El rol de '{rol}' no es una opcion valida."]
            })
        return data

    def create(self, validated_data):
        user = get_user_model().objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            rol_usuario=validated_data.get('rol_usuario', User.Roles.USUARIO_NORMAL),
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
        token['rol_usuario'] = user.rol_usuario

        return token