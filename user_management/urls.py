from django.urls import path
from user_management.views import UserCreate

app_name = 'user_management'

urlpatterns = [
    path('signup/', UserCreate.as_view(), name='signup'),
]
