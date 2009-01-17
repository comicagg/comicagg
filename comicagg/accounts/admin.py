from django.contrib import admin
from comic_ak.accounts.models import *

class UserProfileAdmin(admin.ModelAdmin):
  list_display = ('user', 'last_read_access',)
  ordering = ('user', )

admin.site.register(UserProfile, UserProfileAdmin)
