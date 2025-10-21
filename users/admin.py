from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Añadimos el campo 'role' en la sección de información adicional
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Rol y permisos adicionales', {'fields': ('role',)}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Rol', {'fields': ('role',)}),
    )

    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name',
        'role', 'is_staff', 'is_active', 'is_superuser'
    )
    list_filter = ('role', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('id',)


admin.site.site_header = "Panel Administración API"
admin.site.site_title = "Admin API"
admin.site.index_title = "Gestión de datos"