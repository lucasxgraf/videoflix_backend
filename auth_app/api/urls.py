from django.urls import path

from .views import RegistrationView, ActivationView, CookieTokenObtainPairView, LogoutView, CookieTokenRefreshView

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('activate/<uidb64>/<token>/', ActivationView.as_view(), name='activate'),
    path('login/', CookieTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
]