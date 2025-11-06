from rest_framework.permissions import BasePermission
class IsFormOwnerOrCoordinator(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        if getattr(user, 'is_staff', False) or getattr(user, 'role', None) == 'VCM' or user.groups.filter(name__in=['vcm']).exists():
            return True
        return obj.subject.teacher_id == user.id
