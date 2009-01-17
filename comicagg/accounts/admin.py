from django.contrib import admin
from comicagg.accounts.models import *

class UserProfileAdmin(admin.ModelAdmin):
  list_display = ('user', 'last_read_access',)
  ordering = ('user', )

admin.site.register(UserProfile, UserProfileAdmin)
