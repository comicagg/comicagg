# -*- coding: utf-8 -*-
from django.contrib import admin
from comicagg.accounts.models import *

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'last_read_access','is_active')
    ordering = ('user', )
    actions = ['activate_user', 'deactivate_user']

    def activate_user(self, request, queryset):
        for obj in queryset:
            obj.user.is_active=True
            obj.user.save()
        self.message_user(request, "Usuarios activados")
    activate_user.short_description = "Activar usuario(s)"

    def deactivate_user(self, request, queryset):
        for obj in queryset:
            obj.user.is_active=False
            obj.user.save()
        self.message_user(request, "Usuarios desactivados")
    deactivate_user.short_description = "Desactivar usuario(s)"

admin.site.register(UserProfile, UserProfileAdmin)
