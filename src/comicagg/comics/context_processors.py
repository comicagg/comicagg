from django.db.models import Count
from django.http import HttpRequest


def comic_counters(request: HttpRequest):
    add_context = {
        "unread_count": 0,
        "newcomic_count": 0,
        "news_count": 0,
        "comic_count": 0,
    }
    if request.user.is_authenticated:
        add_context["unread_count"] = request.user.unreadcomic_set.exclude(
            comic__active=False, comic__ended=False
        ).aggregate(Count("comic", distinct=True))["comic__count"]
        add_context["newcomic_count"] = request.user.newcomic_set.exclude(
            comic__active=False
        ).count()
        add_context["news_count"] = request.user.newblog_set.count()
        add_context["comic_count"] = request.user.subscription_set.exclude(
            comic__active=False, comic__ended=False
        ).count()
    return add_context
