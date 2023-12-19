from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from comicagg.comics.models import (
    Comic,
    Strip,
    NewComic,
    Request,
    Subscription,
    Tag,
    UnreadStrip,
)

# ##############
# #   Comics   #
# ##############


class TagInline(admin.TabularInline):
    model = Tag
    ordering = (
        "name",
        "comic",
    )
    extra = 0


class HasCustomFunction(admin.SimpleListFilter):
    title = _("custom function")
    parameter_name = "custom"

    def lookups(self, request: Any, model_admin: Any) -> list[tuple[Any, str]]:
        return [
            ("true", "Custom function"),
            ("false", "Default function"),
        ]

    def queryset(self, request: Any, queryset: QuerySet[Any]) -> QuerySet[Any] | None:
        if self.value() == "true":
            return queryset.exclude(Q(custom_func__isnull=True) | Q(custom_func=""))
        elif self.value() == "false":
            return queryset.filter(Q(custom_func__isnull=True) | Q(custom_func=""))


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
                "fields": (
                    "re1_url",
                    "re1_base",
                    "re1_re",
                    "re1_backwards",
                    "referrer",
                ),
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
    list_filter = ["active", HasCustomFunction]


# TODO: inline with comics?
class StripAdmin(admin.ModelAdmin):
    list_display = (
        "comic",
        "date",
        "url",
    )
    search_fields = ["comic__name"]
    ordering = ("-date",)


# TODO: inline with users?
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


# TODO: inline with users?
class UnreadStripAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "comic",
        "strip",
    )
    search_fields = ["user__username"]


# TODO: inline with users?
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
admin.site.register(Strip, StripAdmin)
admin.site.register(UnreadStrip, UnreadStripAdmin)
admin.site.register(NewComic, NewComicAdmin)
