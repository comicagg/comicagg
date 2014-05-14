from comicagg.comics.models import Comic, ComicHistory
from email import utils
import json, time

class Serializer:
    def __init__(self, user=None, xml=False):
        """
        xml determines if the output is XML or JSON. By defaul it's JSON.
        """
        self.user = user
        self.prefer_xml = xml

    def serialize(self, what=None, last_strip=False, unread_strips=False, identifier=None):
        """
        Pass an instance of Comic, ComicHistory, a list of Comic instances or a dictionary to get a serialized version.
        If what is a list or a dict, then identifier will be used as the container name.
        """
        d = dict()
        if type(what) is Comic:
            d["comic"] = self.build_comic_dict(what, last_strip, unread_strips)
        elif type(what) is ComicHistory:
            d["strip"] = self.build_comichistory_dict(what)
        elif type(what) is list and identifier:
            d[identifier] = [self.build_comic_dict(x, last_strip, unread_strips) for x in what]
        elif type(what) is dict and identifier:
            d[identifier] = what
        elif not what and self.user:
            d["user"] = self.build_user_dict()
        else:
            raise ValueError("Object to serialize is not valid or you are missing another parameter (identifier?)")

        if not self.prefer_xml:
            return json.dumps(d, separators=(',', ':'))
        return build_xml(d)

    def build_comic_dict(self, comic, last_strip=False, unread_strips=False):
        if not type(comic) is Comic:
            raise ValueError("This is not a comic")
        if not self.user:
            raise ValueError("To serialize a comic you need an user")
        out = dict()
        if self.prefer_xml:
            out["__class"] = "comic"
        out["id"] = comic.id
        out["name"] = comic.name
        out["website"] = comic.website
        out["votes"] = comic.votes
        out["rating"] = comic.get_rating()
        out["added"] = str(self.user.get_profile().is_subscribed(comic))
        out["unreadcount"] = self.user.get_profile().unread_comic_strips_count(comic)
        if last_strip:
            out["laststrip"] = self.build_comichistory_dict(comic.comichistory_set.all()[0])
        if unread_strips:
            out["unreads"] = [self.build_comichistory_dict(h) for h in self.user.get_profile().unread_comic_strips(comic)]
        return out

    def build_comichistory_dict(self, history):
        out = dict()
        if self.prefer_xml:
            out["__class"] = "strip"
        out["id"] = history.id
        out["imageurl"] = history.image_url()
        out["imagetext"] = history.alt_text if history.alt_text else ""
        out["date"] = datetime_to_rfc2822(history.date)
        out["timestamp"] = long(datetime_to_timestamp(history.date))
        return out

    def build_user_dict(self):
        out = dict()
        if self.prefer_xml:
            out["__class"] = "user"
        out["username"] = self.user.username
        out["email"] = "" # TODO do we really want/need to return this?
        out["totalcomics"] = len(self.user.get_profile().all_comics())
        out["unreadcomics"] = len(self.user.get_profile().unread_comics())
        return out

def build_xml(what):
    """
    what should be a dictionary with only one key which will be the root element
    """
    if len(what.keys()) != 1:
        raise ValueError
    out = '<?xml version="1.0" encoding="UTF-8" ?>\r\n'
    for k,v in what.items():
        out += build_xml_element(k, v)
    return out

def build_xml_element(name, value):
    # First, we need to check if the value is a dict or a list
    # If value is dict, then parse all values
    # If any value is a dict or list, then this element will need opening and closing tags
    # While parsing the values, build a dict with the values that are scalar as they'll be attributes
    # In the end, write the string
    # If the value passed is a list, then we need just to create opening and closing tags using name and recurse
    if type(value) is list:
        out = "<%s>%s</%s>" % (
            name,
            ''.join([build_xml_element(None, x) for x in value]),
            name)
    else:
        attx = dict()
        child = None
        for k,v in value.items():
            if type(v) is dict:
                child = build_xml_element(v["__class"], v)
            elif type(v) is list:
                child = ''.join([build_xml_element(None, x) for x in v])
            else:
                attx[k] = v

        tag = name if name else attx["__class"]
        out = "<" + tag
        if len(attx):
            out += " "
            out += " ".join(['%s="%s"' % (k,v) for k,v in attx.items() if not k.startswith("__")])
        if child:
            out += ">" + child + "</" + tag + ">"
        else:
            out += "/>"
    return out

def datetime_to_timestamp(dt):
    tup = dt.timetuple()
    return time.mktime(tup)

def datetime_to_rfc2822(dt):
    return utils.formatdate(datetime_to_timestamp(dt))