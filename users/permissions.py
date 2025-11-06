from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    #Solo ADMIN puede escribir; otros solo GET
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'role', None) == 'ADMIN')


class IsAdminOrDAC(BasePermission):
    """Permite acciones solo a ADMIN o DAC; requiere autenticación.

    - Lectura: permite a cualquier usuario autenticado (si la vista lo admite).
    - Escritura: limita a roles ADMIN o DAC.
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        role = getattr(user, 'role', None)
        return role in ('ADMIN', 'DAC')
