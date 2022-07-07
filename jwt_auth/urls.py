from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView
)


app_name = 'jwt_auth'

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
