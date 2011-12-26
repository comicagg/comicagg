/*jslint white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, newcap: true, immed: true, strict: true */
/*global window, document, setTimeout, $, $$, Date, Image, Ajax, Element, media_url, url_mark_all_read, url_mark_as_read, url_remove, url_report, openurl, startRequest, comicCounter, unreadCounter, updateCounters, unreadComics, comics */
"use strict";
// comic list. Array of divs
var clist = [];
var maxwidth = 0;
// to avoid concurrent uses of updateViewport
var alreadyUpdating = false;
var cdivInView = [];
var divlist = [];

// add a bit in the url to make it different so browser caching won't happen
function addSeed(url) {
    var date = new Date();
    if (url.indexOf('?') === -1) {
        url += "?" + date.getTime();
    } else {
        url += "&" + date.getTime();
    }
    return url;
}
// loads an image from url and puts it in elem
function loadImage(url, elem, comic) {
    var img;
    img = new Image();
    elem.cid = comic.id;
    img.onload = function () {
        elem.src = url;
        if (this.width > maxwidth) {
            elem.style.width = "100%";
        }
    };
    img.onerror = function () {
        elem.alt = "ERROR";
        elem.src = media_url + 'images/error.png';
        comics[elem.cid].error = true;
        $('reload' + elem.cid).show();
    };
    img.src = url;
}
// will load the images of this comic if it hasnt been loaded yet.
// if seed is true, it will add a seed in the image url
function loadComic(comic, seed) {
    var s, i, unread, image, url;
    maxwidth = $('c' + comic.id).select('.comicextra')[0].getDimensions().width;
    if (!comic.loaded) {
        s = 'reload' + comic.id;
        $(s).hide();
        for (i = 0; i < comic.list.length; i = i + 1) {
            unread = comic.list[i];
            image = $('imgu' + unread.unreadid);
            url = seed ? addSeed(unread.url) : unread.url;
            loadImage(url, image, comic);
        }
        if (comic.list.length === 0) {
            image = $('imgl' + comic.id);
            url = seed ? addSeed(comic.last_url) : comic.last_url;
            loadImage(url, image, comic);
        }
        comic.loaded = true;
    }
}
function inViewport(cdiv, vmin, vmax) {
    var emin, h, emax, c1, c2, c3;
    emin = cdiv.cumulativeOffset().top;
    h = cdiv.getHeight();
    emax = emin + h;
    c1 = emin <= vmin && emax >= vmax; //sobresale del viewport
    c2 = emin >= vmin && emin <= vmax; //el borde inferior esta dentro
    c3 = emax >= vmin && emax <= vmax; //el borde superior esta dentro
    if (c1 || c2 || c3) {
        return true;
    } else {
        return false;
    }
}
function updateViewport(loadImages) {
    var end, viewp, vmin, vmax, i, len, cdiv, comic;
    if (alreadyUpdating) {
        return 0;
    }
    alreadyUpdating = true;
    //número de comics extras por debajo
    end = 2;
    viewp = false;
    vmin = document.viewport.getScrollOffsets().top;
    vmax = vmin + document.viewport.getHeight();
    cdivInView = [];
    for (i = 0, len = divlist.length; i < len && end > 0; i = i + 1) {
        cdiv = divlist[i];
        // solo afecta a elementos visibles
        if (cdiv.visible()) {
            if (inViewport(cdiv, vmin, vmax)) {
                cdivInView.push(cdiv);
                if (loadImages) {
                    comic = comics[cdiv.id.substring(1)];
                    loadComic(comic, false);
                }
                viewp = true;
            } else {
                if (viewp) {
                    cdivInView.push(cdiv);
                    if (loadImages) {
                        comic = comics[cdiv.id.substring(1)];
                        loadComic(comic, false);
                    }
                    end -= 1;
                }
            }
        }
    }
    alreadyUpdating = false;
}
// first batch load of comic images. will load only those comics in the viewport
function initLoadImages() {
    var lista, div, id, comic;
    updateViewport(false);
    lista = cdivInView;
    while (lista.length > 0) {
        div = lista.shift();
        id = parseInt(div.id.substring(1), 10);
        comic = comics[id];
        if (comic.last_url) {
            loadComic(comic, false);
        }
    }
}
// shows all the comics divs
function showAllComics() {
    var i;
    for (i = 0; i < clist.length; i = i + 1) {
        clist[i].show();
    }
    $('showingAll').show();
    $('showingUnread').hide();
    updateViewport(true);
}
// shows only unread comics divs
function showUnreadComics() {
    var i, cid;
    for (i = 0; i < clist.length; i = i + 1) {
        cid = parseInt(clist[i].id.substring(1), 10);
        if (!unreadComics[cid]) {
            clist[i].hide();
        } else {
            clist[i].show();
        }
    }
    $('showingAll').hide();
    $('showingUnread').show();
    updateViewport(true);
}
function onScrollHandler(e) {
    setTimeout(function () {
        updateViewport(true);
    }, 10);
}
function initScrolling() {
    window.onscroll = onScrollHandler;
    divlist = $$('.comic');
}
// function exed when loading of html ends
function onReadLoad() {
    clist = $$('.comic');
    updateCounters();
    showUnreadComics();
    initScrolling();
    if (comicCounter) {
        if (unreadCounter) {
            initLoadImages();
        } else {
            //TODO mostrar comic aleatorio
            return 0;
        }
    } else {
        $('noComicsSelected').show();
    }
}
// reloads all the images from a comic that had previously failed loading adding a seed in the url
function reloadComic(cid) {
    var comic = comics[cid];
    comic.loaded = false;
    comic.error = false;
    loadComic(comic, true);
}
function markread(id, vote) {
    var ret, params;
    params = {'id': id, 'value': vote};
    Element.show('working' + id);
    Element.hide('workingerror' + id);
    startRequest(url_mark_as_read, {
        method: 'post',
        parameters: params,
        dataType: "json",
        onSuccess: function (counters) {
            Element.hide('working' + id);
            Element.hide('workingerror' + id);
            Element.hide('reading' + id);
            Element.hide('newnotice' + id);
            Element.show('ok' + id);
            setTimeout("Element.hide('ok" + id + "')", 5000);
            unreadComics[id] = false;
            updateCounters(counters);
        },
        onFailure: function (response) {
            //Error
            Element.hide('working' + id);
            Element.show('workingerror' + id);
        },
        onException: function (req, exc) {
            //Error
            Element.hide('working' + id);
            Element.show('workingerror' + id);
        }
    });
}

function reportbroken(id) {
    var list, chids, params, ret;
    chids = [];
    list = comics[id].list;
    if (list.length === 0) {
        //for a read comic
        chids.push(comics[id].last_ch);
    } else {
        //for an unread comic
        list.each(function (item) {
            chids.push(item.chid);
        });
    }
    params = {'id': id, 'chids[]': chids};
    Element.show('working' + id);
    Element.hide('workingerror' + id);
    startRequest(url_report, {
        method: 'post',
        parameters: params,
        onSuccess: function (response) {
            Element.hide('working' + id);
            Element.hide('workingerror' + id);
            Element.show('ok' + id);
            setTimeout("Element.hide('ok" + id + "')", 5000);
        },
        onFailure: function (response) {
            //Error
            Element.hide('working' + id);
            Element.show('workingerror' + id);
        },
        onException: function (req, exc) {
            //Error
            Element.hide('working' + id);
            Element.show('workingerror' + id);
        }
    });
}

function removecomic(id) {
    var params, cdiv, mover_a;
    params = {'id': id};
    Element.show('working' + id);
    startRequest(url_remove, {
        method: 'post',
        parameters: params,
        dataType: "json",
        onSuccess: function (counters) {
            //update counters
            updateCounters(counters);
            //quitar el comic de la principal
            cdiv = $('c' + id);
            //siguiente div hermano
            mover_a = cdiv.next();
            //buscamos uno que sea visible ahora mismo
            while (mover_a !== null && mover_a !== undefined && !mover_a.visible()) {
                mover_a = mover_a.next();
            }
            if (mover_a === null || mover_a === undefined) {
                //no hay siguiente, pues anterior
                mover_a = cdiv.previous();
                //buscamos uno que sea visible ahora mismo
                while (mover_a !== null && mover_a !== undefined && !mover_a.visible()) {
                    mover_a = mover_a.previous();
                }
            }
            //ocultar el div y quitarlo del dom
            cdiv.hide();
            cdiv.remove();
            //quitarlo de las listas
            comics[id] = null;
            unreadComics[id] = null;
            //no quedan comics en la lista, mostrar aviso
            if ($('comics').childElements().length === 0) {
                $('noComicsSelected').show();
            } else if (mover_a !== null && mover_a !== undefined) {
                mover_a.scrollToExtra(-40);
            }
        },
        onFailure: function (response) {
            //Error
            Element.hide('working' + id);
            Element.show('workingerror' + id);
        },
        onException: function (req, exc) {
            //Error
            Element.hide('working' + id);
            Element.show('workingerror' + id);
        }
    });
}
function mark_all_read() { //TODO
    var i;
    $("mark_all_read_anim").show();
    startRequest(url_mark_all_read, {
        dataType: "json",
        onSuccess: function (counters) {
            $("mark_all_read_anim").hide();
            //update counters and arrays
            updateCounters(response.responseJSON);
            for (i = 0; i < unreadComics.length; i = i + 1) {
                unreadComics[i] = false; 
            }
            //now we hide every comic
            showUnreadComics();
            //hide link to mark all read
            $("mark_all_read").hide();
        },
        onFailure: function () {
            $("mark_all_read_anim").hide();
        }
    });
}
