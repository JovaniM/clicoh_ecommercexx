from django.urls import path
from user_management.views import UserCreate

from user_management.views import Protegida  # REMOVE
app_name = 'user_management'

urlpatterns = [
    path('signup/', UserCreate.as_view(), name='signup'),
    path('protegida', Protegida.as_view(), name='protegida')
]
