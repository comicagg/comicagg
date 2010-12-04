# -*- coding: utf-8 -*-
from django.contrib import admin
from comicagg.todo.models import Task

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'state', 'date', )
    search_fields = []
    ordering = ('state', 'date', )
    save_on_top = True

admin.site.register(Task, TaskAdmin)
