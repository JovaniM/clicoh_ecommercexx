from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import AllowAny
from user_management.serializers import UserSerializer


from rest_framework.response import Response  # REMOVE
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


class UserCreate(generics.CreateAPIView):
    user_model = get_user_model()
    queryset = user_model.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny, )
