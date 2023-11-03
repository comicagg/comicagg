from django.contrib import admin

from comicagg.comics.models import (
    Comic,
    ComicHistory,
    NewComic,
    Request,
    Subscription,
    Tag,
    UnreadComic,
)


class TagInline(admin.TabularInline):
    model = Tag
    ordering = (
        "name",
        "comic",
    )


class ComicAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "active",
        "ended",
        "last_update",
    )
    search_fields = ["name"]
    save_on_top = True
    inlines = [
        TagInline,
    ]
    fieldsets = (
        (
            "Comic details",
            {"fields": ("name", "website", "active", "ended", "notify", "no_images")},
        ),
        (
            "Image regex",
            {
                "classes": ("wide",),
                "fields": ("re1_url", "re1_base", "re1_re", "re1_backwards", "referrer"),
            },
        ),
        (
            "Redirection regex",
            {
                "classes": (
                    "collapse",
                    "wide",
                ),
                "fields": ("re2_url", "re2_base", "re2_re", "re2_backwards"),
            },
        ),
        (
            "Custom update function",
            {"classes": ("collapse",), "fields": ("custom_func",)},
        ),
        (
            "Votes",
            {"classes": ("collapse",), "fields": ("positive_votes", "total_votes")},
        ),
        (
            "Last update",
            {
                "fields": (
                    "last_update",
                    "last_update_status",
                    "last_image",
                    "last_image_alt_text",
                )
            },
        ),
    )


class ComicHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "comic",
        "date",
        "url",
    )
    search_fields = ["comic__name"]
    ordering = ("-date",)


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "comic",
    )
    search_fields = ["user__username"]
    ordering = (
        "user",
        "position",
    )


class UnreadComicAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "comic",
        "history",
    )
    search_fields = ["user__username"]


class NewComicAdmin(admin.ModelAdmin):
    ordering = (
        "user",
        "comic",
    )
    search_fields = ["user__username", "comic__name"]


class RequestAdmin(admin.ModelAdmin):
    list_display = ("url", "user", "done", "rejected")
    ordering = ("done",)


admin.site.register(Comic, ComicAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Request, RequestAdmin)
admin.site.register(ComicHistory, ComicHistoryAdmin)
admin.site.register(UnreadComic, UnreadComicAdmin)
admin.site.register(NewComic, NewComicAdmin)
