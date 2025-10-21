from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from .models import Subject
from .serializers import SubjectSerializer
from .permissions import IsSubjectTeacherOrAdmin

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().select_related('teacher')
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsSubjectTeacherOrAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False) or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(teacher=user)
