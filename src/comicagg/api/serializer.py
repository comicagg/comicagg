import contextlib
import time
from email import utils

from comicagg.accounts.models import User
from comicagg.comics.models import Comic, Strip
from comicagg.comics.update import InvalidParameterException


# ########################
# #   Helper functions   #
# ########################


def _datetime_to_timestamp(datetime):
    time_tuple = datetime.timetuple()
    return time.mktime(time_tuple)


def _datetime_to_rfc2822(datetime):
    return utils.formatdate(_datetime_to_timestamp(datetime))


class Serializer:
    """
    This class is used to serialize the data that has to be sent in the response of the API.

    Could be merged with the APIView class but like this it's easier to separate the work of both classes.
    """

    def __init__(self, user: User | None = None):
        self.user = user

    def serialize(
        self,
        object_to_serialize=None,
        include_last_strip=False,
        include_unread_strips=False,
        identifier=None,
    ):
        """Serializes an instance of Comic, Strip, a list of Comic instances or a dictionary.

        If object_to_serialize is a list or a dict, then identifier will be used as the container name.
        """
        result = {}
        if isinstance(object_to_serialize, Comic):
            # Serialize a Comic object
            result["comic"] = self.build_comic_dict(
                object_to_serialize, include_last_strip, include_unread_strips
            )
        elif isinstance(object_to_serialize, Strip):
            # Serialize a Strip object (strip)
            result["strip"] = self.build_strip_dict(object_to_serialize)
        elif isinstance(object_to_serialize, list) and identifier:
            # Serialize a list of Comic objects using identifier as the parent element
            if len(object_to_serialize) == 0:
                # This clause could be joined with the next one with an or,
                # but it's easier to read like this
                result[identifier] = []
            elif isinstance(object_to_serialize[0], Comic):
                # This is a list of comics
                result[identifier] = [
                    self.build_comic_dict(x, include_last_strip, include_unread_strips)
                    for x in object_to_serialize
                ]
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
            raise ValueError(
                "Object to serialize is not valid. Are you missing a parameter (identifier)?"
            )

        return result

    def build_comic_dict(self, comic, last_strip=False, unread_strips=False):
        if not isinstance(comic, Comic):
            raise ValueError("This is not a comic")
        if not self.user:
            raise ValueError("To serialize a comic you need a user")
        out = {
            "id": comic.id,
            "name": comic.name,
            "website": comic.website,
            "votes": comic.total_votes,
            "rating": comic.get_rating(),
            "added": self.user.is_subscribed(comic),
            "ended": comic.status == Comic.ComicStatus.ENDED,
            "unread_count": self.user.unread_strips_for(comic).count(),
        }
        if last_strip:
            with contextlib.suppress(Exception):
                out["last_strip"] = self.build_strip_dict(comic.last_strip)
        if unread_strips:
            out["unreads"] = [
                self.build_strip_dict(h) for h in self.user.unread_strips_for(comic)
            ]
        return out

    def build_strip_dict(self, strip):
        return {
            "id": strip.id,
            "url": strip.image_url(),
            "text": strip.alt_text or "",
            "date": _datetime_to_rfc2822(strip.date),
            "timestamp": _datetime_to_timestamp(strip.date),
        }

    def build_user_dict(self):
        if not self.user:
            raise InvalidParameterException(["self.user"])
        return {
            "username": self.user.username,
            "email": self.user.email,
            "total_comics": self.user.subscription_count(),
            "unread_comics": self.user.comics_unread_count(),
            "new_comics": self.user.comics_new_count(),
        }
