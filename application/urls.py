from django.contrib import admin
from django.urls import path
from django.urls import include 
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('requests.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
