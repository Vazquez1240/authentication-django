from rest_framework.decorators import action
from .managers import CustomRefreshToken
from .models import User
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken, TokenBackendError
from rest_framework import viewsets, status
from .permissions import IsAuthenticatedAndObjUserOrIsStaff
from rest_framework import exceptions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
import jwt
from users.settings import users_auth_settings

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser]
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
    http_method_names = ['post', 'options', 'head', 'patch']
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.validate(request.data):
            user = serializer.create(request.data)
            return Response({'status': '201'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['patch'], detail=False, url_path='create-username', url_name='create-username')
    def create_username(self, request):
        if self.request.data.get('email') is None or self.request.data.get('username') is None:
            return Response({'error': 'Email and username are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=self.request.data.get('email'))
        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        user.username = self.request.data.get('username')

        if User.objects.filter(username=self.request.data.get('username')).exists():
            return Response({"username": "Este nombre de usuario ya esta en uso."}, status=status.HTTP_400_BAD_REQUEST)

        user.save()

        serializer = UserSerializer(user)

        return Response(serializer.data)

class AuthTokenViewset(viewsets.ViewSet):

    http_method_names = ['post', 'options', 'head']
    permission_classes = [AllowAny]

    def create(self, request):
        view = CustomTokenObtainPairView.as_view()
        try:
            response = view(request._request)
            data = response.data



            if 'refresh' in data and 'access' in data:
                access_token = data.get('access')
                decoded_access = jwt.decode(
                    access_token, users_auth_settings.SECRET_KEY,
                    algorithms=[users_auth_settings.TOKEN_ALGORITHM])

                return Response({
                    'refresh': data['refresh'],
                    'access': data['access'],
                    'user_id': decoded_access['user_id'],
                    'is_superuser': decoded_access['is_superuser'],
                    'uuid': decoded_access['uuid'],
                    'rol_usuario': decoded_access['rol_usuario'],
                }, status=status.HTTP_200_OK)
            else:
                if 'No active account found with the given credentials' in data['detail']:
                    return Response({
                                        'error': 'No se encontró ninguna cuenta activa con las credenciales proporcionadas, verifique sus datos!'},
                                    status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'error': 'Credenciales inválidas o respuesta inesperada del servidor de autenticación.'
            }, status=status.HTTP_400_BAD_REQUEST)

        except TokenError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidToken as e:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        except TokenBackendError as e:
            return Response({'error': 'Token backend error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LogoutViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedAndObjUserOrIsStaff]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['post', 'options', 'head']

    def create(self, request):
        try:

            refresh_token = request.data.get('refresh')
            token = CustomRefreshToken(refresh_token)
            token.blacklist()

            return Response({'token': 'Delete token'}, status=status.HTTP_205_RESET_CONTENT)

        except TokenError as e:
            return Response({'error':'El token ya se encuentra en la lista negra'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print('entrando a exception')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TokenRefreshViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def create(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

            refresh = CustomRefreshToken(refresh_token)
            refresh.verify()
            access_token = refresh.get_new_access_token()

            data = {
                'access': access_token,
                'refresh': str(refresh)
            }
            return Response(data, status=status.HTTP_200_OK)
        except TokenError as e:
             return Response({'error': 'Refresh token is invalid.'},
                                status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({'error': f'Unexpected error occurred: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)