/*jslint white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, newcap: true, immed: true, strict: true */
/*global window, document, setTimeout, $, $$, Date, Image, Ajax, Element, static_url, url_mark_all_read, url_mark_as_read, url_remove, url_report, openurl, startRequest, comicCounter, unreadCounter, updateCounters, unreadComics, comics */
"use strict";
// comic list. Array of divs
var clist = [];
var maxwidth = 0;
// to avoid concurrent uses of updateViewport
var alreadyUpdating = false;
//list of comic <div> currently in the viewport + extra(s)
var cdivInView = [];
//real number of current comics in the viewport
var cdivInViewCount = 0;
//list of comic <div> that will be checked for the viewport 
var divlist = [];
//controls whether to show the next comic bar or not
var showNextComicBar = false;
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
        elem.src = static_url + 'images/error.png';
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
/* Checks that the passed <div> is inside the viewport
 */
function inViewport(cdiv, vmin, vmax) {
    var emin, h, emax, c1, c2, c3;
    //top of the element
    emin = cdiv.cumulativeOffset().top;
    h = cdiv.getHeight();
    //bottom of the element
    emax = emin + h;
    //all the element occupies the viewport. top and bottom are beyond the viewport
    c1 = emin <= vmin && emax >= vmax;
    //top border is inside the viewport
    c2 = emin >= vmin && emin <= vmax;
    //bottom border is inside the vieport
    c3 = emax >= vmin && emax <= vmax;
    console.log("comic id " + cdiv.id + (c1 ? " full" : "") + (c2 ? " top" : "") + (c3 ? " bottom" : ""));
    if (c1 || c2 || c3) {
        return true;
    } else {
        return false;
    }
}
/* Updates viewport information (ie. which comics are currently in the viewport).
 * When loadImages is true it will load the comics currently in the viewport (and those extra below it)
 */
function updateViewport(loadImages) {
    var extras, viewp, vmin, vmax, i, len, cdiv, comic;
    //semaphore so we don't run this function more than once at a time' 
    if (alreadyUpdating) {
        return 0;
    }
    alreadyUpdating = true;
    //end is the number of extra comics below the viewport.
    //we always want at least one so when the user scrolls down the next comic
    //should always be already loaded
    extras = 1;
    //controls that we have reached the viewport
    // viewp == 0: havent reached the viewport yet
    // viewp == 1: inside the viewport
    // viewp == 2: passed the viewport
    viewp = 0;
    //vertical position of the viewport: top + top bar
    vmin = document.viewport.getScrollOffsets().top + 40;
    //vertical position of the viewport: bottom
    vmax = vmin + document.viewport.getHeight();
    //<div> in the viewport
    cdivInView = [];
    cdivInViewCount = 0;
    //iterate the list of divs to control
    //we will iterate until we have checked all the items in the list
    //OR we have reached the last item in the viewport and the extra items below it
    for (i = 0, len = divlist.length; i < len && (viewp < 2 || extras > 0); i = i + 1) {
        cdiv = divlist[i];
        //we don't like hidden items
        if (cdiv.visible()) {
            //check that the item is inside the viewport
            if (inViewport(cdiv, vmin, vmax)) {
                //it is!
                cdivInView.push(cdiv);
                cdivInViewCount += 1;
                //load the images of this comics?
                if (loadImages) {
                    comic = comics[cdiv.id.substring(1)];
                    loadComic(comic, false);
                }
                //we are in the viewport
                viewp = 1;
            } else {
                //this item is not in the viewport
                //check if we just left the viewport, ie. this is the next item to be shown if we scrolled down
                //and if we did, check that we allow extra comics
                if (viewp > 0 && extras > 0) {
                    cdivInView.push(cdiv);
                    if (loadImages) {
                        comic = comics[cdiv.id.substring(1)];
                        loadComic(comic, false);
                    }
                    //one extra comic less
                    extras -= 1;
                    viewp = 2;
                }
            }
        }
    }
    //when the length of the array is the same as the counter we are at the bottom
    if (cdivInView.length > cdivInViewCount && showNextComicBar) {
        try {
            cdiv = cdivInView[cdivInViewCount];
            comic = comics[cdiv.id.substring(1)];
            var el = new Element("a", {'onclick': '$("c'+comic.id+'").scrollToExtra(-40)'}).update(comic.name);
            $('next_comic_bar').update(el);
            $('next_comic_bar').show();
        } catch (e) {
            $('next_comic_bar').hide();            
        }
    } else {
        $('next_comic_bar').hide();
    }
    //free the semaphore
    alreadyUpdating = false;
    var s = "";
    for (i = 0; i < cdivInView.length; i = i + 1) {
        var div = cdivInView[i];
        s += div.id + " "
    }
    console.log("divs in view: " + s + " real: " + cdivInViewCount);
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
    $('no_unread_comics').hide();
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
    if (unreadCounter === 0 && comicCounter) {
        $('noUnreadCounters').show();
	$('unreadCounters').hide();
	$('no_unread_comics').show();
    } else {
        $('noUnreadCounters').hide();
        $('unreadCounters').show();
    }
    updateViewport(true);
}
/* Function to handle the scroll event.
 * 10 ms after the event has been launched it will update the viewport information 
 */
function onScrollHandler(e) {
    setTimeout(function () {
        updateViewport(true);
    }, 10);
}
/* Inits the scrolling handler.
 */
function initScrolling() {
    window.onscroll = onScrollHandler;
    //Sets the list of divs to control to all the comic divs
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
            $("no_unread_comics").show();
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
function mark_all_read() {
    var i;
    $("mark_all_read_anim").show();
    startRequest(url_mark_all_read, {
        dataType: "json",
        onSuccess: function (counters) {
            $("mark_all_read_anim").hide();
            //update counters and arrays
            updateCounters(counters);
            for (i = 0; i < unreadComics.length; i = i + 1) {
                unreadComics[i] = false; 
            }
            //now we hide every comic
            showUnreadComics();
            //hide link to mark all read
            $("mark_all_read").hide();
            $("mark_all_read_bottom").hide();
	    $("no_unread_comics").show();
        },
        onFailure: function () {
            $("mark_all_read_anim").hide();
        }
    });
}
