// updates html counters
function updateCounters() {
	if (unreadCounter > 0) {
		document.title = titlei18n + " (" + unreadCounter + ") - " + titlebase;
		$('noUnreadCounter').hide();
		$('unreadCounterP').show();
		$('menuUnreadCounter').innerHTML = ' (' + unreadCounter + ')';
		$('infoUnreadCounter').innerHTML = unreadCounter;
	} else {
		document.title = titlei18n + " - " + titlebase;
		$('noUnreadCounter').show();
		$('unreadCounterP').hide();
		$('menuUnreadCounter').innerHTML = '';
	}
	$('totalComicCounter').innerHTML = comicCounter;
	$('totalComicCounter2').innerHTML = comicCounter;
}
// shows all the comics divs
function showAllComics() {
	for (i = 0; i < clist.length; i++) {
		clist[i].show();
	}
	$('showingAll').show();
	$('showingUnread').hide();
	updateViewport(true);
}
// shows only unread comics divs
function showUnreadComics() {
	for (i = 0; i < clist.length; i++) {
		cid = clist[i].id.substring(1);
		if (!unreadComics[cid]) {
			clist[i].hide();
		}
	}
	$('showingAll').hide();
	$('showingUnread').show();
	updateViewport(true);
}
// comic list. Array of divs
var clist = new Array();

// function exed when loading of html ends
function onReadLoad() {
	updateCounters();
	initScrolling();
	initLoadImages();
	clist = $$('.comic');
}
// first batch load of comic images. will load only those comics in the viewport
function initLoadImages() {
	updateViewport(false);
	lista = cdivInView;
	do {
		div = lista.shift();
		comic = comics[div.id.substring(1)];
		if(comic.last_url) {
			_loadComic(comic, false);
		}
	} while (lista.length > 0);
}
// will load the images of this comic if it hasnt been loaded  yet.
// if seed is true, it will add a seed in the image url
function _loadComic(comic, seed) {
	if(!comic.loaded) {
		s = 'reload' + comic.id;
		$(s).hide();
		for(i = 0; i < comic.list.length; i++) {
			unread = comic.list[i];
			image = $('imgu' + unread.unreadid);
			url = seed ? _addSeed(unread.url) : unread.url;
			_loadImage(url, image, comic);
		}
		if (comic.list.length == 0) {
			image = $('imgl' + comic.id);
			url = seed ? _addSeed(comic.last_url) : comic.last_url;
			_loadImage(url, image, comic);
		}
		comic.loaded = true;
	}
}
// add a bit in the url to make it different so browser caching won't happen
function _addSeed(url) {
	_date = new Date();
	if (url.indexOf('?') == -1) {
		url += "?" + _date.getTime();
	} else {
		url += "&" + _date.getTime();
	}
	return url;
}
// loads an image from url and puts it in elem
function _loadImage(url, elem, comic) {
	img = new Image();
	elem.cid = comic.id;
	img.onload = function () {
		elem.src = url;
	}
	img.onerror = function () {
		elem.alt = "ERROR";
		elem.src = media_url + 'images/error.png';
		comics[elem.cid].error = true;
		$('reload'+elem.cid).show();
	}
	img.src = url;
}
// reloads all the images from a comic that had previously failed loading adding a seed in the url
function reloadComic(cid) {
	comic = comics[cid];
	comic.loaded = false;
	comic.error = false;
	_loadComic(comic, true);
}

/* Scrolling things */

var sync = false;
var cdivInView = new Array();
var divlist = new Array();
function initScrolling() {
	window.onscroll = onScrollHandler;
	divlist = $$('.comic');
}

function onScrollHandler(e) {
	updateViewport(true);
}

function updateViewport(loadImages) {
	if (sync) return;
	sync = true;
	end = 1;
	viewp = false;
	vmin = document.viewport.getScrollOffsets()['top'];
	vmax = vmin + document.viewport.getHeight();
	cdivInView = new Array();
	for (var i = 0, len = divlist.length; i < len && end>0; ++i) {
		cdiv = divlist[i];
		// solo afecta a elementos visibles
		if (cdiv.visible()) {
			if (inViewport(cdiv, vmin, vmax)) {
				cdivInView.push(cdiv);
				if (loadImages) {
					comic = comics[cdiv.id.substring(1)];
					_loadComic(comic, false);
				}
				viewp = true;
			} else {
				if (viewp) {
					cdivInView.push(cdiv);
					if (loadImages) {
						comic = comics[cdiv.id.substring(1)];
						_loadComic(comic, false);
					}
					end -= 1;
				}
			}
		}
	}
	sync = false;
}

function inViewport(cdiv, vmin, vmax) {
	emin = cdiv.cumulativeOffset()['top'];
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

/* AJAX */

function markread(id, vote) {
	var url = url_mark_as_read;
	var params = {'id': id, 'value':vote };
	Element.show('working' + id);
	new Ajax.Request(url, {
		method: 'post',
		parameters: params,
		onSuccess: function(transport) {
			if(transport.status == 0) {
				//Error
				Element.hide('working'+id);
				Element.show('workingerror'+id);
			} else {
				ret = transport.responseText;
				if (ret==0) {
					Element.hide('working'+id);
					Element.hide('workingerror'+id);
					Element.hide('reading'+id);
					Element.hide('newnotice'+id);
					unreadCounter--;
					unreadComics[id] = false;
					updateCounters();
				}
				else {
					//Error
					Element.hide('working'+id);
					Element.show('workingerror'+id);
				}
			}
		},
		onFailure: function(transport) {
			//Error
			Element.hide('working'+id);
			Element.show('workingerror'+id);
		},
		onException: function(req, exc) {
			//Error
			Element.hide('working'+id);
			Element.show('workingerror'+id);
		}
	});
}

function reportbroken(id) {
	var url = url_report;
	var params = {'id': id};
	Element.show('working' + id);
	new Ajax.Request(url, {
		method: 'post',
		parameters: params,
		onSuccess: function(transport) {
			if(transport.status == 0) {
				//Error
				Element.hide('working'+id);
				Element.show('workingerror'+id);
			} else {
				ret = transport.responseText;
				if (ret==0) {
					Element.hide('working'+id);
					Element.hide('workingerror'+id);
				}
				else {
					//Error
					Element.hide('working'+id);
					Element.show('workingerror'+id);
				}
			}
		},
		onFailure: function(transport) {
			//Error
			Element.hide('working'+id);
			Element.show('workingerror'+id);
		},
		onException: function(req, exc) {
			//Error
			Element.hide('working'+id);
			Element.show('workingerror'+id);
		}
	});
}
