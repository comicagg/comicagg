import json
import time
from email import utils
from comicagg.comics.models import Comic, ComicHistory
from comicagg.comics.utils import UserOperations

class Serializer:
    """
    This class is used to serialize the data that has to be sent in the response of the API.

    Could be merged with the APIView class but like this it's easier to separate the work of both classes.
    """

    def __init__(self, user=None):
        self.user = user

    def serialize(self, object_to_serialize=None, include_last_strip=False, include_unread_strips=False, identifier=None):
        """Serializes an instance of Comic, ComicHistory, a list of Comic instances or a dictionary.

        If object_to_serialize is a list or a dict, then identifier will be used as the container name.
        """
        result = dict()
        if isinstance(object_to_serialize, Comic):
            # Serialize a Comic object
            result["comic"] = self.build_comic_dict(object_to_serialize, include_last_strip, include_unread_strips)
        elif isinstance(object_to_serialize, ComicHistory):
            # Serialize a ComicHistory object (strip)
            result["strip"] = self.build_comichistory_dict(object_to_serialize)
        elif isinstance(object_to_serialize, list) and identifier:
            # Serialize a list of Comic objects using identifier as the parent element
            if len(object_to_serialize) == 0:
                # This clause could be joined with the next one with an or, but it's easier to read like this
                result[identifier] = []
            elif isinstance(object_to_serialize[0], Comic):
                # This is a list of comics
                result[identifier] = [self.build_comic_dict(x, include_last_strip, include_unread_strips) for x in object_to_serialize]
            else:
                # This is a list of integers
                result[identifier] = object_to_serialize
        elif isinstance(object_to_serialize, dict) and identifier:
            # Serialize a dictionary of objects using identifier as the parent element
            result[identifier] = object_to_serialize
        elif not object_to_serialize and self.user:
            # Serialize the current user information if there is no object_to_serialize
            result["user"] = self.build_user_dict()
        else:
            raise ValueError("Object to serialize is not valid. Are you missing a parameter (identifier)?")

        return result

    def build_comic_dict(self, comic, last_strip=False, unread_strips=False):
        if not isinstance(comic, Comic):
            raise ValueError("This is not a comic")
        if not self.user:
            raise ValueError("To serialize a comic you need a user")
        user_operations = UserOperations(self.user)
        out = dict()
        out["id"] = comic.id
        out["name"] = comic.name
        out["website"] = comic.website
        out["votes"] = comic.total_votes
        out["rating"] = comic.get_rating()
        out["added"] = user_operations.is_subscribed(comic)
        out["ended"] = comic.ended
        out["unread_count"] = user_operations.unread_comic_strips_count(comic)
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
        out["id"] = history.id
        out["url"] = history.image_url()
        out["text"] = history.alt_text if history.alt_text else ""
        out["date"] = datetime_to_rfc2822(history.date)
        out["timestamp"] = datetime_to_timestamp(history.date)
        return out

    def build_user_dict(self):
        user_operations = UserOperations(self.user)
        out = dict()
        out["username"] = self.user.username
        out["email"] = self.user.email
        out["total_comics"] = len(user_operations.subscribed_comics())
        out["unread_comics"] = len(user_operations.unread_comics())
        out["new_comics"] = user_operations.new_comics().count()
        return out

# Helper functions

def datetime_to_timestamp(datetime):
    tuple = datetime.timetuple()
    return time.mktime(tuple)

def datetime_to_rfc2822(datetime):
    return utils.formatdate(datetime_to_timestamp(datetime))
