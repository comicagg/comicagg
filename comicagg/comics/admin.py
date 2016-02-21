# -*- coding: utf-8 -*-
from django.contrib import admin
from comicagg.comics.models import Comic, ComicHistory, NewComic, Request, Subscription, Tag, UnreadComic

class TagInline(admin.TabularInline):
    model = Tag
    ordering = ('name', 'comic',)

class ComicAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'ended', 'last_update', )
    search_fields = ['name']
    save_on_top = True
    inlines = [TagInline,]
    fieldsets = (
        ('Comic details', {
            'fields' : ('name', 'website', 'active', 'ended', 'notify', 'no_images')
        }),
        ('Image regex', {
            'classes': ('wide', ),
            'fields' : ('url', 'base_img', 'regexp', 'backwards')
        }),
        ('Redirection regex', {
            'classes': ('collapse', 'wide', ),
            'fields' : ('url2', 'base2', 'regexp2', 'backwards2')
        }),
        ('Custom update function', {
            'classes': ('collapse',),
            'fields' : ('custom_func',)
        }),
        ('Other options', {
            'classes': ('collapse',),
            'fields' : ('referer',)
        }),
        ('Votes', {
            'classes': ('collapse',),
            'fields' : ('positive_votes', 'total_votes')
        }),
        ('Last image', {
            'fields' : ('last_update', 'last_image', 'last_image_alt_text')
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
