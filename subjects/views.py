from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from .models import Subject, Area, SemesterLevel, CompanyRequirement, Api3Alternance, ApiType2Completion, ApiType3Completion
from .serializers import SubjectSerializer, AreaSerializer, SemesterLevelSerializer, CompanyRequirementSerializer, Api3AlternanceSerializer, ApiType2CompletionSerializer, ApiType3CompletionSerializer
from .permissions import IsSubjectTeacherOrAdmin


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().select_related('teacher', 'area')
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsSubjectTeacherOrAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False) or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(teacher=user)


class AreaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Area.objects.all().order_by('name')
    serializer_class = AreaSerializer
    permission_classes = [permissions.IsAuthenticated]


class SubjectSemesterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SemesterLevel.objects.all().order_by('id')
    serializer_class = SemesterLevelSerializer
    permission_classes = [permissions.IsAuthenticated]


class CompanyRequirementViewSet(viewsets.ModelViewSet):
    queryset = CompanyRequirement.objects.all().select_related('subject', 'company')
    serializer_class = CompanyRequirementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False) or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)


class Api3AlternanceViewSet(viewsets.ModelViewSet):
    queryset = Api3Alternance.objects.all().select_related('subject')
    serializer_class = Api3AlternanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False) or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)


class ApiType2CompletionViewSet(viewsets.ModelViewSet):
    queryset = ApiType2Completion.objects.all().select_related('subject')
    serializer_class = ApiType2CompletionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False) or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)


class ApiType3CompletionViewSet(viewsets.ModelViewSet):
    queryset = ApiType3Completion.objects.all().select_related('subject')
    serializer_class = ApiType3CompletionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False) or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)
