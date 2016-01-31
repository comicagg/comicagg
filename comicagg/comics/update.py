# -*- coding: utf-8 -*-
"""Functions to check if the comics have been updated."""
import re
from datetime import datetime
from html import unescape
from django.conf import settings
import requests
from comicagg.comics.models import ComicHistory, UnreadComic

class NoMatchException(Exception):
    """To be thrown when updating a comic if we did not find the image in the page."""

    def __init__(self, message):
        super(Exception, self).__init__(message)
        self.message = message

    def __str__(self):
        return repr(self.message)

def update_comic(comic):
    """Entry point to trigger an update in a comic."""
    has_changed = False
    # We may need to use a custom update function
    if comic.custom_func:
        has_changed = custom_update(comic)
    else:
        comic_history = default_update(comic)
        if comic_history:
            notify_subscribers(comic_history)
            has_changed = True
    return has_changed

def custom_update(comic):
    """Wrapper for the custom update function.
    
    A custom update function must fill in the list history_set with the ComicHistory objects it has found.
    The most recent strip found must be the first in the list."""
    history_set = list()

    function_text = comic.custom_func.replace('\r', '')
    function_compiled = compile(function_text, '<string>', 'exec')
    exec(function_compiled)
    if history_set:
        # If the first image of the list is the same as the comic's last_image, abandon ship
        if comic.last_image == history_set[0].url:
            return False
        # Update the comic
        comic.last_image = history_set[0].url
        comic.last_image_alt_text = history_set[0].alt_text
        comic.last_update = datetime.now()
        comic.save()
        # Persist the ComicHistory objects in the database
        for history in history_set:
            history.save()
            notify_subscribers(history)
        return True
    raise NoMatchException("%s" % comic.name)

def default_update(comic):
    """Default update function. Looks for just one image in the URL.
    
    If the comic doesn't use a redirection, then we will download the default URL and then search with the regex in that data.
    If it uses a redirection, then it will download the redirection URL and look for the final URL there."""
    if comic.url2:
        next_url = get_redirected_url(comic)
    else:
        next_url = comic.url

    # Here next_url should be the URL where the comic strip is
    (last_image, alt_text) = get_one_image(comic, next_url)

    # At this point, last_image should be completely clean,
    # meaning that it should be URL encoded if needed
    if last_image == comic.last_image:
        return None
    comic.last_image = last_image
    comic.last_image_alt_text = alt_text
    comic.last_update = datetime.now()
    history = ComicHistory(comic=comic, url=comic.last_image, alt_text=alt_text)
    history.save()
    comic.save()
    return history

def get_several_images(comic, history_set):
    """This function looks for several images in the same page."""
    lines = download_url(comic.url)
    #for debugging
    lines_debug = list(lines)
    (match, lines) = find_match(comic, lines, comic.regexp, comic.backwards)
    while match:
        image_url = comic.base_img % url_from_match(match)
        alt_text = alt_from_match(match)
        history = ComicHistory(comic=comic, url=image_url, alt_text=alt_text)
        history_set.append(history)
        (match, lines) = find_match(lines, comic.regexp, comic.backwards)

# Auxiliary functions needed during update operations
def download_url(url):
    """Download the data from the URL and return the lines of the response."""
    # Clean the URL
    url = unescape(url)
    # NOTE: why did we need the cookie jar before?
    headers = {'User-Agent': settings.USER_AGENT}
    response = requests.get(url, headers=headers)
    lines = [line for line in response.iter_lines()]
    return lines

def find_match(remaining_lines, regexp, backwards=False):
    """Find a match in the remaining lines using the regex and returning a tuple containing the match object and the remaining lines to review."""
    # Set the pop index, depending on how we need to look for a match.
    pop_index = 0
    if backwards:
        pop_index = -1

    regex_text = r'%s' % regexp
    regex_compiled = re.compile(regex_text)
    match = None
    while len(remaining_lines) > 0:
        line = remaining_lines.pop(pop_index)
        # FUTURE: should we use django.utils.encoding.smart_text instead?
        try:
            line = line.decode('utf-8')
        except:
            pass
        match = regex_compiled.search(line)
        if match:
            break
    return (match, remaining_lines)

def get_one_image(comic, url):
    """Find one image in this URL."""
    lines = download_url(url)
    # We use this field to be able to debug the NoMatchException in case it fails
    lines_debug = list(lines)
    (match, lines) = find_match(lines, comic.regexp, comic.backwards)
    if not match:
        raise NoMatchException("%s" % comic.name)
    image_url = comic.base_img % url_from_match(match)
    alt_text = alt_from_match(match)
    return (image_url, alt_text)

def get_redirected_url(comic):
    """Find the final URL using the redirection in the comic."""
    lines = download_url(comic.url2)
    # We use this field to be able to debug the NoMatchException in case it fails
    lines_debug = list(lines)
    (match, lines) = find_match(lines, comic.regexp2, comic.backwards2)
    if not match:
        raise NoMatchException("%s" % comic.name)
    next_url = comic.base2 % url_from_match(match)
    return next_url

def url_from_match(match):
    """Return the URL from the match object.
    
    The URL should be on the named group. We check the first group too, just in case."""
    try:
        url = match.group("url")
    except IndexError:
        url = match.group(1)
    # Unescape the URL
    return unescape(url)

def alt_from_match(match):
    """Return the alternative text if the named group exists."""
    try:
        alt = match.group("alt")
    except IndexError:
        alt = None
    if alt:
        # FUTURE: should we use smart_text here?
        try:
            alt = unicode(alt, 'utf-8')
        except:
            try:
                alt = unicode(alt, 'iso-8859-1')
            except:
                pass
    return alt

def notify_subscribers(history):
    """Create one UnreadComic for each subscribed user."""
    subscribers = history.comic.subscription_set.all()
    for subscriber in subscribers:
        if subscriber.user.is_active:
            UnreadComic.objects.get_or_create(user=subscriber.user, history=history, comic=subscriber.comic)
