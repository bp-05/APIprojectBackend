from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from .models import Semester
from .serializers import SemesterSerializer

class SemesterViewSet(viewsets.ModelViewSet):
    queryset = Semester.objects.all().order_by('-starts_at')
    serializer_class = SemesterSerializer
    permission_classes = [permissions.IsAuthenticated]