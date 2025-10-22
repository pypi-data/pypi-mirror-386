from django.urls import path
from .views import CasClientLoginApiView, CasClientLogoutApiView

urlpatterns = [
    path('login/v1', CasClientLoginApiView.as_view(), name='login'),
    path('logout/v1', CasClientLogoutApiView.as_view(), name='logout')
]