/*jslint white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, newcap: true, immed: true, strict: true */
/*global document, window, $, $$, url_forget_new_blogs, titlei18n, titlebase, unreadCounter: true, comicCounter: true, newComicCounter: true, newsCounter: true, Ajax, Element, dojo*/
"use strict";
function focusOnLogin() {
    $('id_username').focus();
}

function openurl(url) {
    window.open(url);
    return false;
}

function startRequest(url, options) {
    return new Ajax.Request(url, options);
}

function removeComicId(array, comicid) {
    var found = false, i, len, comic;
    for (i = 0, len = array.length; i < len && !found; i = i + 1) {
        comic = array[i];
        found = comic.id === comicid;
        if (found) {
            array[i] = undefined;
        }
    }
    return found ? comic : found;
}

// updates html counters
function updateCounters(counters) {
    if (typeof counters !== "undefined") {
        unreadCounter = counters.unreads;
        comicCounter = counters.comics;
        newComicCounter = counters.new_comics;
        newsCounter = counters.news;
    }
    //first update the counters in the menu
    if (unreadCounter > 0) {
        $('menuUnreadCounter').innerHTML = ' (' + unreadCounter + ')';
    } else {
        $('menuUnreadCounter').hide();
    }
    if (newComicCounter > 0) {
        $('menuNewComicCounter').innerHTML = ' (' + newComicCounter + ')';
    } else {
        $('menuNewComicCounter').hide();
    }
    if (newsCounter > 0) {
        $('menuNewsCounter').innerHTML = ' (' + newsCounter + ')';
    } else {
        $('menuNewsCounter').hide();
    }
    //if we're in the read page
    if (typeof titlei18n === "string") {
        if (unreadCounter > 0) {
            document.title = titlei18n + " (" + unreadCounter + ") - " + titlebase;
            $('noUnreadCounters').hide();
            $('unreadCounters').show();
            $('unreadCountersUnread').innerHTML = unreadCounter;
            $('unreadCountersTotal').innerHTML = comicCounter;
        } else {
            document.title = titlei18n + " - " + titlebase;
            $('noUnreadCounters').show();
            $('unreadCounters').hide();
            $('noUnreadCountersTotal').innerHTML = comicCounter;
        }        
    }
    return 0;
}

// **************
// blog
// **************

function forget_news() {
    startRequest(url_forget_new_blogs, {
        method: 'post',
        onSuccess: function (response) {
            if (response.status === 200) {
                updateCounters(response.responseJSON);
            }
        },
        onFailure: function (response) {}
    });
}
