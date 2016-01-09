import json
import time
from email import utils
from comicagg.comics.models import Comic, ComicHistory
from comicagg.comics.utils import UserOperations

class Serializer:
    """
    This class is used to serialize the data that has to be sent in the response to the API.
    Handles the output format, either JSON or XML, being JSON the default one.

    It works by building dictionaries and lists with the data and then convert these to JSON or XML.
    Could be merged with the APIView class but like this it's easier to separate the work of both classes.
    """

    def __init__(self, user=None, client_prefers_xml=False):
        """xml determines if the output is XML or JSON. By defaul it's JSON."""
        self.user = user
        self.client_prefers_xml = client_prefers_xml

    def serialize(self, object_to_serialize=None, include_last_strip=False, include_unread_strips=False, identifier=None):
        """Serializes to XML or JSON an instance of Comic, ComicHistory, a list of Comic instances or a dictionary.

        If object_to_serialize is a list or a dict, then identifier will be used as the container name.
        """
        d = dict()
        if isinstance(object_to_serialize, Comic):
            # Serialize a Comic object
            d["comic"] = self.build_comic_dict(object_to_serialize, include_last_strip, include_unread_strips)
        elif isinstance(object_to_serialize, ComicHistory):
            # Serialize a ComicHistory object (strip)
            d["strip"] = self.build_comichistory_dict(object_to_serialize)
        elif isinstance(object_to_serialize, list) and identifier:
            # Serialize a list of Comic objects using identifier as the parent element
            if len(object_to_serialize) == 0:
                # This clause could be joined with the next one with an or, but it's easier to read like this
                d[identifier] = []
            elif isinstance(object_to_serialize[0], Comic):
                # This is a list of comics
                d[identifier] = [self.build_comic_dict(x, include_last_strip, include_unread_strips) for x in object_to_serialize]
            else:
                # This is a list of integers
                d[identifier] = object_to_serialize
        elif isinstance(object_to_serialize, dict) and identifier:
            # Serialize a dictionary of objects using identifier as the parent element
            d[identifier] = object_to_serialize
        elif not object_to_serialize and self.user:
            # Serialize the current user information if there is no object_to_serialize
            d["user"] = self.build_user_dict()
        else:
            raise ValueError("Object to serialize is not valid. Are you missing a parameter (identifier)?")

        if not self.client_prefers_xml:
            return json.dumps(d, separators=(',', ':'))
        return build_xml(d)

    def build_comic_dict(self, comic, last_strip=False, unread_strips=False):
        if not isinstance(comic, Comic):
            raise ValueError("This is not a comic")
        if not self.user:
            raise ValueError("To serialize a comic you need a user")
        user_operations = UserOperations(self.user)
        out = dict()
        if self.client_prefers_xml:
            out["__class"] = "comic"
        out["id"] = comic.id
        out["name"] = comic.name
        out["website"] = comic.website
        out["votes"] = comic.votes
        out["rating"] = comic.get_rating()
        out["added"] = str(user_operations.is_subscribed(comic))
        out["ended"] = str(comic.ended)
        out["unreadcount"] = user_operations.unread_comic_strips_count(comic)
        if last_strip:
            try:
                out["last_strip"] = self.build_comichistory_dict(comic.last_strip())
            except:
                pass
        if unread_strips:
            out["unreads"] = [self.build_comichistory_dict(h) for h in user_operations.unread_comic_strips(comic)]
        return out

    def build_comichistory_dict(self, history):
        out = dict()
        if self.client_prefers_xml:
            out["__class"] = "strip"
        out["id"] = history.id
        out["imageurl"] = history.image_url()
        out["imagetext"] = history.alt_text if history.alt_text else ""
        out["date"] = datetime_to_rfc2822(history.date)
        out["timestamp"] = datetime_to_timestamp(history.date)
        return out

    def build_user_dict(self):
        user_operations = UserOperations(self.user)
        out = dict()
        if self.client_prefers_xml:
            out["__class"] = "user"
        out["username"] = self.user.username
        out["email"] = self.user.email
        out["totalcomics"] = len(user_operations.subscribed_comics())
        out["unreadcomics"] = len(user_operations.unread_comics())
        # TODO: Return also the number of new comics
        return out

# Helper functions

def build_xml(dictionary):
    """It will convert a dict to a XML string.

    what should be a dictionary with only one key which will be the root element.
    """
    if len(dictionary.keys()) != 1:
        raise ValueError("The base Dictionary can only contain one item")
    out = '<?xml version="1.0" encoding="UTF-8" ?>\r\n'
    for key, value in dictionary.items():
        out += build_xml_element(key, value)
    return out

def build_xml_element(tag_name, tag_content):
    """Builds a XML element whose tag is name and the content is value. Value will be parsed to XML accordingly."""
    out = ""
    if isinstance(tag_content, list) and len(tag_content) > 0 and isinstance(tag_content[0], int):
        # This is a list of integers
        out = "<%s>%s</%s>" % (
            tag_name,
            ''.join(["<id>%s</id>" % number for number in tag_content]),
            tag_name)
    elif isinstance(tag_content, list):
        # If the value passed is a list, then we need just to create opening and closing tags using name and recurse
        out = "<%s>%s</%s>" % (
            tag_name,
            ''.join([build_xml_element(None, item) for item in tag_content]),
            tag_name)
    elif isinstance(tag_content, dict):
        # If value is dict, then parse all values
        attributes = dict()
        child = None
        for key, value in tag_content.items():
            if isinstance(value, dict):
                # If any value is a dict or list, then this element will need opening and closing tags
                child = build_xml_element(value["__class"], value)
            elif isinstance(value, list):
                # NOTE: If lists should not be wrapped inside an element
                # child = ''.join([build_xml_element(None, x) for x in v])
                child = build_xml_element(key, value)
            else:
                # While parsing the values, build a dict with the values that are scalar as they'll be attributes
                attributes[key] = value

        tag = tag_name if tag_name else attributes["__class"]
        out = "<" + tag
        if len(attributes):
            out += " "
            out += " ".join(['%s="%s"' % (key, value) for key, value in attributes.items() if not key.startswith("__")])
        if child:
            out += ">" + child + "</" + tag + ">"
        else:
            out += "/>"
    return out

def datetime_to_timestamp(datetime):
    tuple = datetime.timetuple()
    return time.mktime(tuple)

def datetime_to_rfc2822(datetime):
    return utils.formatdate(datetime_to_timestamp(datetime))
