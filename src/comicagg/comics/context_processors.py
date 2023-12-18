from django.db.models import Count

from comicagg.typings import AuthenticatedHttpRequest


def comic_counters(request: AuthenticatedHttpRequest):
    add_context = {
        "unread_count": 0,
        "newcomic_count": 0,
        "news_count": 0,
        "comic_count": 0,
    }
    if request.user.is_authenticated:
        add_context["unread_count"] = request.user.comics_unread_count()
        add_context["newcomic_count"] = len(request.user.comics_new())
        add_context["news_count"] = request.user.newblog_set.count()
        add_context["comic_count"] = request.user.subscriptions_active().count()
    return add_context
