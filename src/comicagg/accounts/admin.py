from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileAdmin(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "user profile"


class UserAdmin(BaseUserAdmin):
    list_display = ("username", "last_access", "is_active")
    inlines = [UserProfileAdmin]
    actions = ["activate_user", "deactivate_user"]

    @admin.display(description="Last access")
    def last_access(self, obj):
        return obj.user_profile.last_read_access

    @admin.action(description="Activate user")
    def activate_user(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, "Users have been activated")

    @admin.action(description="Deactivate user")
    def deactivate_user(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Users have been deactivated")

    deactivate_user.short_description = "Desactivar usuario(s)"


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
