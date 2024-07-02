# from django.core.cache import cache
from django.template.defaultfilters import slugify

from comicagg.typings import AuthenticatedHttpRequest

from .models import Comic


def comic_counters(request: AuthenticatedHttpRequest):
    add_context = {
        "unread_count": 0,
        "newcomic_count": 0,
        "news_count": 0,
        "comic_count": 0,
    }
    if request.user.is_authenticated:
        add_context["unread_count"] = request.user.comics_unread_count
        add_context["newcomic_count"] = request.user.comics_new_count
        # TODO: news_count should be in its own context processor in the blog app
        add_context["news_count"] = request.user.blogs_new_count
        add_context["comic_count"] = request.user.subscription_count
    return add_context


def comic_lists(request: AuthenticatedHttpRequest):
    add_context = {}
    if request.resolver_match and request.resolver_match.app_name.startswith("comics"):
        # all of the comics
        # all_comics = cache.get("comics.views.add_comics.all_comics")
        # if not all_comics:
        #     all_comics = list(Comic.objects.available().prefetch_related("subscription_set"))
        #     all_comics.sort(key=_slugify_comic)
        #     cache.set("comics.views.add_comics.all_comics", all_comics, 600)
        all_comics = list(
            Comic.objects.available().prefetch_related("subscription_set")
        )
        all_comics.sort(key=_slugify_comic)
        add_context["all_comics"] = all_comics
        add_context["user_comics"] = request.user.comics_subscribed
        add_context["new_comics"] = request.user.comics_new()
    return add_context


def _slugify_comic(comic: Comic) -> str:
    return slugify(str(comic))
