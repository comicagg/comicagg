/*jslint white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, newcap: true, immed: true, strict: true */
/*global document, window, $, $$, url_forget_new_blogs, titlei18n, titlebase, unreadCounter: true, comicCounter: true, newComicCounter: true, newsCounter: true, Ajax, Element, dojo, $j*/
"use strict";

var newMethods = {
    scrollToExtra:function(element, n) {
        element = $(element);
        var pos = Element.cumulativeOffset(element);
        window.scrollTo(pos[0], pos[1] + n);
        return element; }
    };

Element.addMethods(newMethods);

$j(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

function focusOnLogin() {
    $('id_username').focus();
}

function openurl(url) {
    window.open(url);
    return false;
}

function startRequest(url, options) {
    // set as default data type "text"
    var dataType = options.dataType ?
        options.dataType : "text";
    return jQuery.ajax(
        url, {
            type: options.method,
            data: options.parameters, //array, key-value
            dataType: dataType,
            success: function (data, textStatus, jqXHR){ options.onSuccess(data) }, //success(data, textStatus, jqXHR)
            error: function (jqXHR, textStatus, errorThrown) { options.onFailure(jqXHR) }, //error(jqXHR, textStatus, errorThrown)
    });
    //return new Ajax.Request(url, options);
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
        if($('mark_all_read')) {
            $('mark_all_read').hide();
        }
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
