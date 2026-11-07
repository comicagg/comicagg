/*jslint white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, newcap: true, immed: true, strict: true */
/*global document, window, setTimeout, clearTimeout, byId, showElement, hideElement, documentOffset, openurl */
"use strict";
let comics;
let lastevent;
let timerid;
let currentid = 0;

function onclick_url(event) {
    event.preventDefault();
    event.stopPropagation();
    openurl(byId("comic_url").href);
}

function containsComicId(array, comicid) {
    var found = false, i, len, comic;
    for (i = 0, len = array.length; i < len && !found; i += 1) {
        comic = array[i];
        found = comic.id === comicid;
    }
    return found ? comic : found;
}

let idFilter = -1;

function filter(keyword) {
    clearTimeout(idFilter);
    idFilter = setTimeout(() => applyFilter(keyword), 100);
}

const isRunningComic = (css_classes) => {
    return css_classes.indexOf('broken') === -1 && css_classes.indexOf('ended') === -1
};

function applyFilter(keyword) {
    const comics = byId('comic_list').children;
    for (let comic of comics) {
        let comic_keywords = comic.innerHTML.toLowerCase();
        let css_classes = comic.className.split(" ");
        css_classes.forEach(css_class => {
            comic_keywords += " @" + css_class;
        });
        if (isRunningComic(css_classes)) {
            comic_keywords += " @running"
        }
        if (keyword.length > 0 && comic_keywords.indexOf(keyword) < 0) {
            hideElement(comic);
        } else {
            showElement(comic);
        }
    };
}

function filter_all() {
    byId("search_box").value = "";
    filter("");
}

function filter_new() {
    byId("search_box").value = "@new";
    filter("@new");
}

function filter_running() {
    byId("search_box").value = "@running";
    filter("@running");
}

function filter_added() {
    byId("search_box").value = "@added";
    filter("@added");
}

function last_image_onerror() {
    showElement(byId('last_image_broken'));
    hideElement(byId('last_image'));
}

function last_image_onload() {
    hideElement(byId('last_image_broken'));
    showElement(byId('last_image'));
    update_comic_image_height();
}

function update_comic_image_height() {
    const info_offset = documentOffset(byId('comic_info')).top;
    const info_height = byId('comic_info').offsetHeight;
    const image_offset = documentOffset(byId('last_image')).top;
    const image_height = info_height + info_offset - image_offset;
    document.documentElement.style.setProperty('--comic-image-height', image_height + "px");
}

function _calculateComicListHeight() {
    console.log(`window ${window.innerWidth} x ${window.innerHeight}`);
    console.log(`viewport ${document.documentElement.clientWidth} x ${document.documentElement.clientHeight}`);

    const scrollbar_width = window.innerWidth - document.documentElement.clientWidth;
    document.documentElement.style.setProperty('--scrollbar-width', scrollbar_width + "px");

    const comic_list_height = document.documentElement.clientHeight - scrollbar_width - documentOffset(byId('comic_list')).top;
    document.documentElement.style.setProperty('--comic-list-height', comic_list_height + "px");
}
// recalculate on resize
window.addEventListener('resize', _calculateComicListHeight, false);
// recalculate on dom load
document.addEventListener('DOMContentLoaded', _calculateComicListHeight, false);
// recalculate on load (assets loaded as well)
window.addEventListener('load', _calculateComicListHeight);
