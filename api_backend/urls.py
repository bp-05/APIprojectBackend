"""
URL configuration for api_backend project.

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
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Import user views
from users.views import MeViewSet, UserViewSet

# Import other app views
from semesters.views import SemesterViewSet
from subjects.views import SubjectViewSet
from forms_app.views import FormInstanceViewSet, FormTemplateViewSet
from descriptors.views import DescriptorViewSet

# Configure router
router = DefaultRouter()
# User routes
router.register(r'users/me', MeViewSet, basename='users-me')
router.register(r'users', UserViewSet, basename='users')

# Other app routes
router.register(r'semesters', SemesterViewSet, basename='semester')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'forms', FormInstanceViewSet, basename='forminstance')
router.register(r'form-templates', FormTemplateViewSet, basename='formtemplate')
router.register(r'descriptors', DescriptorViewSet, basename='descriptor')

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API
    path('api/', include(router.urls)),
    path('api/', include('exports_app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
