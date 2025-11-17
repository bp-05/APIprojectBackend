from rest_framework.permissions import BasePermission


class IsSubjectTeacherOrAdmin(BasePermission):
    """
    Docente: solo ve/edita sus asignaturas.
    Admin/Coordinador (grupo 'vcm' o is_staff): acceso amplio.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if (
            getattr(user, 'is_staff', False)
            or getattr(user, 'role', None) in ['DAC', 'VCM', 'COORD', 'DC']
            or user.groups.filter(name__in=['vcm']).exists()
        ):
            return True
        return obj.teacher_id == user.id


class IsAdminOrCoordinator(BasePermission):
    """
    Solo Admin/Coordinador (o staff) pueden administrar configuraciones globales.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_staff', False):
            return True
        return getattr(user, 'role', None) in {'ADMIN', 'COORD'}
