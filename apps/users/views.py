import logging

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
 
from .models import User
from .serializers import RegisterSerializer, UserProfileSerializer
# Create your views here.

logger = logging.getLogger(__name__)

class RegisterView(generics.CreateAPIView):
    """Register a new user (student or instructor)."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)


    def create(self, request, *args, **kwargs):
        logger.debug(
            'Register attempt: username=%s email=%s role=%s',
            request.data.get('username'),
            request.data.get('email'),
            request.data.get('role'),
        )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
 
        logger.info('New user registered: %s (role: %s)', user.email, user.role)

        # Return tokens on registration so user is immediately logged in
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=201) 
    

class MeView(generics.RetrieveUpdateAPIView):
    """Get or update the currently authenticated user's profile."""
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        logger.debug('Fetching profile for user: %s', self.request.user.email)
        return self.request.user