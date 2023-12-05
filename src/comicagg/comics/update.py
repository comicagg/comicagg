"""Functions to check if the comics have been updated."""

import contextlib
import re
from datetime import datetime, timezone
from html import unescape

import requests
from comicagg.comics.models import Comic, ComicHistory, UnreadComic
from django.conf import settings


class NoMatchException(Exception):
    """To be thrown when updating a comic if we did not find the image in the page."""

    def __init__(self, message: str):
        super(Exception, self).__init__(message)
        self.message = message

    def __str__(self):
        return repr(self.message)

class InvalidParameterException(Exception):
    def __init__(self, parameters: list[str]):
        message = f"Invalid parameters: {", ".join(parameters)}"
        super(Exception, self).__init__(message)
        self.message = message

    def __str__(self):
        return repr(self.message)

def update_comic(comic: Comic) -> bool:
    """Entry point to trigger an update in a comic."""
    has_changed = False
    # We may need to use a custom update function
    if comic.custom_func:
        has_changed = _custom_update(comic)
    elif comic_history := _default_update(comic):
        _notify_subscribers(comic_history)
        has_changed = True
    return has_changed


def _custom_update(comic: Comic) -> bool:
    # sourcery skip: move-assign-in-block, use-named-expression
    """Wrapper for the custom update function.

    A custom update function must fill in the list history_set with the ComicHistory objects it has found.
    The most recent strip found must be the first in the list."""
    if not comic.custom_func:
        return False
    function_text = comic.custom_func.replace("\r", "")
    function_compiled = compile(function_text, "<string>", "exec")
    history_set: list[ComicHistory] = []
    exec(function_compiled)
    if history_set:
        # If the first image of the list is the same as the comic's last_image, abandon ship
        if comic.last_image == history_set[0].url:
            return False
        # Update the comic
        comic.last_image = history_set[0].url
        comic.last_image_alt_text = history_set[0].alt_text
        comic.last_update = datetime.now(timezone.utc)
        comic.save()
        # Persist the ComicHistory objects in the database
        for history in history_set:
            history.save()
            _notify_subscribers(history)
        return True
    raise NoMatchException(comic.name)


def _default_update(comic: Comic) -> ComicHistory | None:
    """Default update function. Looks for just one image in the URL.

    If the comic doesn't use a redirection, then we will download the default URL and then search with the regex in that data.
    If it uses a redirection, then it will download the redirection URL and look for the final URL there.
    """
    if not comic.re1_url:
        return None
    next_url = _get_redirected_url(comic) if comic.re2_url else comic.re1_url

    # Here next_url should be the URL where the comic strip is
    (last_image, alt_text) = _get_one_image(comic, next_url)

    # At this point, last_image should be completely clean,
    # meaning that it should be URL encoded if needed
    if last_image == comic.last_image:
        return None
    comic.last_image = last_image
    comic.last_image_alt_text = alt_text
    comic.last_update = datetime.now(timezone.utc)
    history = ComicHistory(comic=comic, url=comic.last_image, alt_text=alt_text)
    history.save()
    comic.save()
    return history


def _get_several_images(comic: Comic, history_set: list[ComicHistory]):
    """This function looks for several images in the same page."""
    if not comic.re1_url or not comic.re1_base or not comic.re1_re or not comic.re1_backwards:
        return
    lines = _download_url(comic.re1_url)
    (match, lines) = _find_match(lines, comic.re1_re, comic.re1_backwards)
    while match:
        image_url = comic.re1_base % _url_from_match(match)
        alt_text = _alt_from_match(match)
        history = ComicHistory(comic=comic, url=image_url, alt_text=alt_text)
        history_set.append(history)
        (match, lines) = _find_match(lines, comic.re1_re, comic.re1_backwards)


# Auxiliary functions needed during update operations
def _download_url(url: str) -> list[str]:
    """Download the data from the URL and return the lines of the response."""
    # Clean the URL
    url = unescape(url)
    # NOTE: why did we need the cookie jar before?
    headers = {"User-Agent": settings.USER_AGENT}
    response = requests.get(url, headers=headers)
    return list(response.iter_lines(decode_unicode=True))


def _find_match(
    remaining_lines: list[str], regexp: str, backwards=False
) -> tuple[re.Match[str] | None, list[str]]:
    """Find a match in the remaining lines using the regex
    and return a tuple containing the match object and the remaining lines to review."""
    # Set the pop index, depending on how we need to look for a match.
    pop_index = -1 if backwards else 0
    regex_compiled = re.compile(regexp)
    match = None
    while remaining_lines:
        line = remaining_lines.pop(pop_index)
        match = regex_compiled.search(line)
        if match:
            break
    return (match, remaining_lines)


def _get_one_image(comic: Comic, url) -> tuple[str, str]:
    """Find one image in this URL."""
    if not comic.re1_base or not comic.re1_re:
        raise InvalidParameterException(["re1_base", "re1_re"])
    lines = _download_url(url)
    # We use this field to be able to debug the NoMatchException in case it fails
    (match, lines) = _find_match(lines, comic.re1_re, comic.re1_backwards)
    if not match:
        raise NoMatchException(comic.name)
    image_url = comic.re1_base % _url_from_match(match)
    alt_text = _alt_from_match(match)
    return (image_url, alt_text)


def _get_redirected_url(comic: Comic) -> str:
    """Find the final URL using the redirection in the comic."""
    if not comic.re2_url or not comic.re2_base or not comic.re2_re:
        raise InvalidParameterException(["re1_base", "re1_re"])
    lines = _download_url(comic.re2_url)
    # We use this field to be able to debug the NoMatchException in case it fails
    (match, lines) = _find_match(lines, comic.re2_re, comic.re2_backwards)
    if not match:
        raise NoMatchException(comic.name)
    return comic.re2_base % _url_from_match(match)


def _url_from_match(match: re.Match) -> str:
    """Return the URL from the match object.

    The URL should be on the named group. We check the first group too, just in case."""
    try:
        url = match["url"]
    except IndexError:
        url = match[1]
    return unescape(url)


def _alt_from_match(match) -> str:
    """Return the alternative text if the named group exists."""
    alt = ""
    with contextlib.suppress():
        alt = match.group("alt")
    return alt


def _notify_subscribers(history: ComicHistory):
    """Create one UnreadComic for each subscribed user."""
    subscribers = history.comic.subscription_set.all()
    for subscriber in subscribers:
        if subscriber.user.is_active:
            UnreadComic.objects.get_or_create(
                user=subscriber.user, history=history, comic=subscriber.comic
            )
