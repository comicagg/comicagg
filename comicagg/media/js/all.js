/*jslint white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, newcap: true, immed: true, strict: true */
/*global window, $, $$, url_forget_new_blogs, Ajax, Element, dojo*/
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
// **************
// blog
// **************

function forget_new_posts() {
    startRequest(url_forget_new_blogs, {
        method: 'post',
        onSuccess: function (response) {
            if (response.status === 200) {
                $("menuNewNewsCounter").innerHTML = "";
            }
        },
        onFailure: function (response) {}
    });
}
