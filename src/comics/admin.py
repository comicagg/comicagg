from typing import Any

from django.contrib import admin
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _
from django.http import HttpRequest

from .fields import ComicStatus
from .models import Comic, NewComic, Request, Strip, Subscription, Tag, UnreadStrip
from .tasks.update_comics import update_comic_task

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


class HasCustomFunctionFilter(admin.SimpleListFilter):
    title = _("custom function")
    parameter_name = "custom"

    def lookups(
        self, request: HttpRequest, model_admin: "ComicAdmin"
    ) -> list[tuple[str, str]]:
        return [
            ("true", "Custom function"),
            ("false", "Default function"),
        ]

    def queryset(
        self, request: HttpRequest, queryset: QuerySet[Comic]
    ) -> QuerySet[Comic] | None:
        if self.value() == "true":
            return queryset.exclude(Q(custom_func__isnull=True) | Q(custom_func=""))
        elif self.value() == "false":
            return queryset.filter(Q(custom_func__isnull=True) | Q(custom_func=""))


class LastUpdateFilter(admin.SimpleListFilter):
    title = _("last update status")
    parameter_name = "status"

    def lookups(self, request: Any, model_admin: "ComicAdmin") -> list[tuple[Any, str]]:
        return [
            ("success", "Success"),
            ("nomatch", "No match"),
            ("error", "Error"),
        ]

    def queryset(
        self, request: Any, queryset: QuerySet[Comic]
    ) -> QuerySet[Comic] | None:
        if self.value() == "success":
            return queryset.filter(Q(last_update_status="Success"))
        elif self.value() == "nomatch":
            return queryset.filter(Q(last_update_status="No match during update"))
        else:
            return queryset.filter(Q(last_update_status__startswith="Error:"))


@admin.action(description=_("Start update task"))
def update_comic_via_task(
    modeladmin: "ComicAdmin", request: HttpRequest, queryset: QuerySet[Comic]
):
    for comic in queryset:
        update_comic_task.apply_async(
            (comic.id,), periodic_task_name=f"Update comic {comic.id}"
        )


@admin.action(description=_("Mark as active"))
def mark_as_active(
    modeladmin: "ComicAdmin", request: HttpRequest, queryset: QuerySet[Comic]
):
    queryset.update(status=ComicStatus.ACTIVE)


@admin.action(description=_("Mark as broken"))
def mark_as_broken(
    modeladmin: "ComicAdmin", request: HttpRequest, queryset: QuerySet[Comic]
):
    queryset.update(status=ComicStatus.BROKEN)


class ComicAdmin(admin.ModelAdmin):
    actions = [update_comic_via_task, mark_as_active, mark_as_broken]
    list_display = ("name", "status", "last_update", "last_update_status")
    search_fields = ["name"]
    save_on_top = True
    inlines = [
        TagInline,
    ]
    fieldsets = (
        (
            "Comic details",
            {
                "fields": (
                    "name",
                    "website",
                    "status",
                    "no_images",
                    "notify",
                )
            },
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
    list_filter = ["status", "no_images", HasCustomFunctionFilter, LastUpdateFilter]


class StripAdmin(admin.ModelAdmin):
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


class UnreadStripAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "comic",
        "strip",
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
admin.site.register(Strip, StripAdmin)
admin.site.register(UnreadStrip, UnreadStripAdmin)
admin.site.register(NewComic, NewComicAdmin)
