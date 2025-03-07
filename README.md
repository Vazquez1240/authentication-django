# Django Users Authentication 🔐

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![JWT](https://img.shields.io/badge/JWT-Authentication-orange.svg)](https://jwt.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful Django authentication library that simplifies user management in your Django projects. This library eliminates the need to create separate authentication apps by providing ready-to-use endpoints for user registration, login, logout, and token management (both access and refresh tokens).

## ✨ Features

- 👤 Custom User Model with email-based authentication
- 🔒 JWT Authentication (access and refresh tokens)
- 🚀 Ready-to-use endpoints for:
  - User Registration
  - Login
  - Logout
  - Token Refresh
- ⚙️ Easy integration with existing Django projects
- 🛡️ Built-in security features

## 🚀 Installation

```bash
pip install django-users-auth
```

## 📦 Structure

The library consists of two main apps:

### 1. Users App

Handles all user-related functionality including:
- Custom User Model
- Authentication Views
- JWT Token Management
- User Permissions

#### Key Files

##### 1. models.py
Defines the custom user model that uses email as the primary identifier.

```python
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from .managers import CustomUserManager
from django.db.models.signals import pre_delete
from django.contrib.auth.models import Group as OriginalGroup
from django.dispatch import receiver
import uuid

class User(AbstractUser):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True)
    username = models.CharField(
        "username",
        max_length=150,
        validators=[UnicodeUsernameValidator()],
        error_messages={"unique": "Ya existe un usuario con ese nombre de usuario."},
    )
    groups = models.ManyToManyField(
        OriginalGroup,
        related_name='custom_user_groups',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()
```

**Detalles de la Clase User:**

- **Campos:**
  - `id`: Clave primaria autoincremental
  - `uuid`: Identificador único universal, generado automáticamente
  - `email`: Campo único para autenticación del usuario
  - `username`: Nombre de usuario con validación Unicode
  - `groups`: Relación ManyToMany con grupos personalizados
  - `user_permissions`: Permisos específicos del usuario

- **Características Principales:**
  - Utiliza UUID para identificación única
  - Autenticación basada en email
  - Validación personalizada de nombre de usuario
  - Relaciones personalizadas de grupos y permisos
  - Manejo de señales para eliminación segura

##### 2. serializers.py
Handles data serialization and validation for the REST API.

```python
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    username = serializers.CharField(write_only=True)
    uuid = serializers.CharField()

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password', 'uuid']
        extra_kwargs = {'password': {'write_only': True}}

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
```

**Detalles de los Serializadores:**

1. **UserSerializer:**
   - **Campos:**
     - `password`: Campo de escritura con validación de contraseña
     - `username`: Campo de escritura para nombre de usuario
     - `uuid`: Identificador único
     - `email`: Email del usuario
   - **Métodos:**
     - `validate`: Verifica la unicidad del email
     - `create`: Crea un nuevo usuario con datos validados

2. **CustomTokenObtainPairSerializer:**
   - **Funcionalidad:**
     - Extiende TokenObtainPairSerializer
     - Añade información adicional al token:
       - Estado de superusuario
       - Estado de staff
       - ID de usuario
       - UUID

##### 3. managers.py
Implements custom user management and JWT authentication logic.

```python
from django.contrib.auth.base_user import BaseUserManager
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if not password:
            password = BaseUserManager.make_random_password(self)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except InvalidToken as e:
            if 'refresh' in str(e):
                raise AuthenticationFailed('Refresh token is invalid or expired. Please log in again.')
            else:
                raise AuthenticationFailed('Access token is invalid. Please refresh your token.')
        except TokenError as e:
            raise AuthenticationFailed(f'Token error: {str(e)}')
```

**Detalles de los Managers:**

1. **CustomUserManager:**
   - **create_user(email, password, **extra_fields):**
     - Crea un usuario normal
     - Valida y normaliza el email
     - Genera contraseña automática si no se proporciona
     - Guarda el usuario en la base de datos

   - **create_superuser(email, password, **extra_fields):**
     - Crea un superusuario
     - Establece permisos de staff y superusuario
     - Hereda la funcionalidad de create_user

2. **CustomJWTAuthentication:**
   - Manejo detallado de errores de token
   - Mensajes específicos para tokens inválidos o expirados
   - Gestión separada de tokens de acceso y actualización

##### 4. permissions.py
Defines custom permission classes for access control.

```python
from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

class IsAuthenticatedAndSelfOrIsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS or
            request.user and
            request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (request.user == obj or request.user.is_superuser)

class IsAuthenticatedAndObjUserOrIsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS or
            request.user and
            request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (request.user == obj.user or request.user.is_superuser)
```

**Detalles de los Permisos:**

1. **IsAuthenticatedAndSelfOrIsStaff:**
   - **has_permission:**
     - Permite métodos seguros (GET, HEAD, OPTIONS)
     - Verifica autenticación del usuario
   - **has_object_permission:**
     - Permite acceso al propio usuario
     - Permite acceso a staff y superusuarios

2. **IsAuthenticatedAndObjUserOrIsStaff:**
   - Similar al anterior pero para objetos relacionados
   - Verifica la relación usuario-objeto
   - Control granular de permisos a nivel de objeto

##### 5. viewsets.py
Implements ViewSets for handling user-related operations.

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from .permissions import IsAuthenticatedAndObjUserOrIsStaff

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedAndObjUserOrIsStaff]
    http_method_names = ['get', 'options', 'head']
    queryset = User.objects.all()

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        elif self.request.user.is_staff:
            return User.objects.all()
        elif self.request.user.is_authenticated:
            return User.objects.filter(pk=self.request.user.pk)
        else:
            raise exceptions.PermissionDenied('Forbidden')

class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.validate(request.data):
            user = serializer.create(request.data)
            return Response({'status': '201'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

**Detalles de los ViewSets:**

1. **CustomTokenObtainPairView:**
   - Personaliza la generación de tokens JWT
   - Utiliza CustomTokenObtainPairSerializer

2. **UserViewSet:**
   - **Configuración:**
     - Métodos permitidos: GET, OPTIONS, HEAD
     - Permisos basados en roles
   - **get_queryset:**
     - Filtra usuarios según permisos
     - Acceso total para superusuarios y staff
     - Acceso limitado para usuarios normales

3. **RegisterViewSet:**
   - Permite registro público (AllowAny)
   - Validación completa de datos
   - Creación segura de usuarios

##### 6. admin.py
Configures the Django admin interface for user management.

```python
from django.contrib import admin
from .models import User, Group
from django.contrib.auth.models import Group as OriginalGroup
from django.contrib import auth

@admin.register(User)
class UserAdmin(auth.admin.UserAdmin):
    list_display = ('email','is_active', 'is_staff', 'uuid')

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        if request.user.is_staff:
            return ('is_staff', 'groups', 'user_permissions')
        return (auth.admin.UserAdmin.fields)

admin.site.register(Group)
admin.site.unregister(OriginalGroup)
```

**Detalles de la Configuración Admin:**

1. **UserAdmin:**
   - **Visualización:**
     - Muestra email, estado activo, estado staff y UUID
   - **Control de Acceso:**
     - Superusuarios: acceso total
     - Staff: campos restringidos
     - Usuarios normales: solo lectura

2. **Gestión de Grupos:**
   - Registro personalizado de grupos
   - Integración con modelo de usuario personalizado
   - Desregistro del modelo Group original

### 2. Base App

The Base app provides core functionality and base models for the authentication system. It serves as the foundation for the Users app and includes essential configurations.

## 🔧 Complete Configuration

To fully integrate the authentication system, add these settings to your `settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'users',
    'base',
]

# User model configuration
AUTH_USER_MODEL = 'users.User'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.managers.CustomJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# JWT settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

## 🛣️ API Endpoints Reference

### Authentication Endpoints

#### 1. User Registration
```http
POST /api/auth/register/
Content-Type: application/json

{
    "email": "user@example.com",
    "username": "username",
    "password": "secure_password123"
}

Response: 201 Created
{
    "status": "201"
}
```

#### 2. User Login
```http
POST /api/auth/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "secure_password123"
}

Response: 200 OK
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user_id": 1,
    "is_superuser": false,
    "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 3. Token Refresh
```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response: 200 OK
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## 🔒 Security Features

1. **Email-Based Authentication**
   - Secure email validation
   - Unique email constraint
   - Custom user manager for email handling

2. **Password Security**
   - Django's password validation
   - Secure password hashing
   - Password strength requirements

3. **JWT Token Security**
   - Access and refresh token mechanism
   - Token expiration and rotation
   - Custom token payload
   - Token blacklisting

4. **Permission System**
   - Role-based access control
   - Object-level permissions
   - Staff and superuser privileges
   - Custom permission classes

5. **Admin Security**
   - Restricted admin access
   - Role-based field restrictions
   - Secure group management

## 🚀 Best Practices

1. **Token Management**
   - Store tokens securely
   - Implement token refresh mechanism
   - Handle token expiration gracefully

2. **Error Handling**
   - Implement proper error responses
   - Validate input data
   - Handle edge cases

3. **Security**
   - Use HTTPS in production
   - Implement rate limiting
   - Follow security headers best practices

4. **User Experience**
   - Implement proper validation messages
   - Handle registration/login flows smoothly
   - Provide clear error messages

### 2. Base App

Provides core functionality and base models for the authentication system. The Base app includes essential utilities that enhance the overall functionality of the authentication system.

#### Key Files

##### 1. managers.py
Implements custom pagination functionality for handling large datasets efficiently.

```python
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class CustomPagination(PageNumberPagination):
    page_size = 250
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        return Response({
            'total_pages': self.page.paginator.num_pages,
            'total_items': self.page.paginator.count,
            'current_page': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })
```

**Details of CustomPagination:**

1. **Configuration:**
   - Default page size: 250 items
   - Configurable page size via query parameter

2. **Enhanced Response Format:**
   - `total_pages`: Total number of available pages
   - `total_items`: Total count of items in the dataset
   - `current_page`: Current page number
   - `next`: URL for the next page
   - `previous`: URL for the previous page
   - `results`: Paginated data

3. **Usage Example:**
```python
from base.managers import CustomPagination

class YourViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination
```

## 🔧 Configuration

Add the following to your `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'users',
    'base',
]

# JWT Authentication settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.managers.CustomJWTAuthentication',
    ]
}
```

## 🛣️ Available Endpoints

- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/token/refresh/` - Refresh access token

## 💻 Usage Example

```python
# Registration
POST /api/auth/register/
{
    "email": "user@example.com",
    "password": "secure_password"
}

# Login
POST /api/auth/login/
{
    "email": "user@example.com",
    "password": "secure_password"
}
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

Martin - [vazquezmartin1240@gmail.com](mailto:vazquezmartin1240@gmail.com)

Project Link: [https://github.com/Vazquez1240/authentication-django](https://github.com/Vazquez1240/authentication-django)

