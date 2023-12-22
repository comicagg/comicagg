# -*- coding: utf-8 -*-
import time
from email.utils import formatdate
from xml.sax.saxutils import escape
from django import template
from comicagg.comics.models import Comic

register = template.Library()

@register.filter
def xml(value, arg=False):
    if isinstance(value, Comic):
        d = {
            "id": value.id,
            "website": escape(value.website),
            "name": escape(value.name),
            "votes": value.total_votes,
            "rating": value.get_rating()
        }
        if bool(arg):
            d["latest.id"] = value.strip_set.latest().id
            d["latest.url"] = escape(value.strip_set.latest().url)
            d["latest.alt_text"] = escape(value.strip_set.latest().alt_text) if value.strip_set.latest().alt_text else ""
            d["latest.date"] = formatdate(time.mktime(value.strip_set.latest().date.timetuple()))
            d["latest.timestamp"] = time.mktime(value.strip_set.latest().date.timetuple())
            output = """<comic id="%(id)d" website="%(website)s" name="%(name)s" votes="%(votes)d" rating="%(rating)f">
            <strip id="%(latest.id)s" imageurl="%(latest.url)s" imagetext="%(latest.alt_text)s" date="%(latest.date)s" timestamp="%(latest.timestamp)d"/>
            </comic>""" % d
        else:
            output = '<comic id="%(id)d" website="%(website)s" name="%(name)s" votes="%(votes)d" rating="%(rating)f"/>' % d
        return output

xml.is_safe = True
