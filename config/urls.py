"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from django.contrib.admindocs import urls as admindocs_urls
from django.conf.urls.static import static
from django.conf import settings
from users.views import (
    CustomLoginView,
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView,
)
from tickets.views import AdminReportView

urlpatterns = [
    # Admin
    path('admin/doc/', include(admindocs_urls)),
    path('admin/', admin.site.urls),
    
    path('', lambda request: redirect('login', permanent=False)),

    # Ticket views
    path('tickets/', include('tickets.urls', namespace='tickets')),

    # Auth views
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Password reset views
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('report/', AdminReportView.as_view(), name='admin_report'),

    path('notifications/', include('notifications.urls', namespace='notifications')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
