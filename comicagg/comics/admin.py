# -*- coding: utf-8 -*-
from comicagg.comics.models import Comic, ComicHistory, NewComic, Request, Subscription, Tag, UnreadComic
from django.contrib import admin

class TagInline(admin.TabularInline):
    model = Tag
    ordering = ('name', 'comic',)

class ComicAdmin(admin.ModelAdmin):
    list_display = ('name', 'activo', 'ended', 'last_check', )
    search_fields = ['name']
    save_on_top = True
    inlines = [TagInline,]
    fieldsets = (
        ('Datos del comic', {
            'fields' : ('name', 'website', 'activo', 'ended', 'notify', 'noimages')
        }),
        ('Configuración básica', {
            'classes': ('wide', ),
            'fields' : ('url', 'base_img', 'regexp', 'backwards')
        }),
        ('Opciones redirección', {
            'classes': ('collapse', 'wide', ),
            'fields' : ('url2', 'base2', 'regexp2', 'backwards2')
        }),
        ('Función personalizada', {
            'classes': ('collapse',),
            'fields' : ('custom_func',)
        }),
        ('Opciones avanzadas', {
            'classes': ('collapse',),
            'fields' : ('referer',)
        }),
        ('Votos', {
            'classes': ('collapse',),
            'fields' : ('rating', 'votes')
        }),
        ('Otros datos', {
            'fields' : ('last_check', 'last_image', 'last_image_alt_text')
        }),
    )
    class Media:
        css = {
            'all': ('css/admin.css', )
        }

class ComicHistoryAdmin(admin.ModelAdmin):
    list_display = ('comic', 'date', 'url',)
    search_fields = ['comic__name']
    ordering = ('-date', )

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'comic',)
    search_fields = ['user__username']
    ordering = ('user', 'position', )

class UnreadComicAdmin(admin.ModelAdmin):
    list_display = ('user', 'comic', 'history',)
    search_fields = ['user__username']

class NewComicAdmin(admin.ModelAdmin):
    ordering = ('user', 'comic',)
    search_fields = ['user__username', 'comic__name']

class RequestAdmin(admin.ModelAdmin):
    list_display = ('url', 'user', 'done', 'rejected')
    ordering = ('done',)

admin.site.register(Comic, ComicAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Request, RequestAdmin)
admin.site.register(ComicHistory, ComicHistoryAdmin)
admin.site.register(UnreadComic, UnreadComicAdmin)
admin.site.register(NewComic, NewComicAdmin)
