from rest_framework.permissions import BasePermission

class IsSubjectTeacherOrAdmin(BasePermission):
    """
    Docente: sólo ve/edita sus asignaturas.
    Admin/Coordinador (grupo 'vcm' o is_staff): acceso amplio.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        if (
            getattr(user, 'is_staff', False)
            or getattr(user, 'role', None) in ['DAC', 'VCM']
            or user.groups.filter(name__in=['vcm']).exists()
        ):
            return True
        return obj.teacher_id == user.id
