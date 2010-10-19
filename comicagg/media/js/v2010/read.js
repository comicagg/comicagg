// updates html counters
function updateCounters() {
	if (unreadCounter > 0) {
		document.title = titlei18n + " (" + unreadCounter + ") - " + titlebase;
		$('noUnreadCounters').hide();
		$('unreadCounters').show();
		$('menuUnreadCounter').innerHTML = ' (' + unreadCounter + ')';
		$('unreadCountersUnread').innerHTML = unreadCounter;
		$('unreadCountersTotal').innerHTML = comicCounter;
	} else {
		document.title = titlei18n + " - " + titlebase;
		$('noUnreadCounters').show();
		$('unreadCounters').hide();
		$('menuUnreadCounter').innerHTML = '';
		$('noUnreadCountersTotal').innerHTML = comicCounter;
	}
	return 0;
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
		} else {
			clist[i].show();
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
	clist = $$('.comic');
	updateCounters();
	showUnreadComics();
	initScrolling();
	if (comicCounter) {
		if (unreadCounter) {
			initLoadImages();
		} else {
			//TODO mostrar comic aleatorio
		}
	} else {
		$('noComicsSelected').show();
	}
}
// first batch load of comic images. will load only those comics in the viewport
function initLoadImages() {
	updateViewport(false);
	lista = cdivInView;
	while (lista.length > 0) {
		div = lista.shift();
		comic = comics[div.id.substring(1)];
		if(comic.last_url) {
			_loadComic(comic, false);
		}
	}
}
var maxwidth = 0;
// will load the images of this comic if it hasnt been loaded  yet.
// if seed is true, it will add a seed in the image url
function _loadComic(comic, seed) {
	maxwidth = $('c'+comic.id).select('.comicextra')[0].getDimensions()['width'];
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
		if (this.width > maxwidth) {
			elem.style.width = "100%";
		}
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
	setTimeout("updateViewport(true)", 10);
}

function updateViewport(loadImages) {
	if (sync) return;
	sync = true;
	//número de comics extras por debajo
	end = 2;
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
//	 $('branding').innerHTML="";
//	 cdivInView.each(function(item){$('branding').innerHTML+=item.id+" "})
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
	var params = {'id': id, 'value':vote };
	Element.show('working' + id);
	Element.hide('workingerror'+id);
	new Ajax.Request(url_mark_as_read, {
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
					Element.show('ok'+id);
					setTimeout("Element.hide('ok" + id + "')", 5000);
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
	var chids = Array();
	list = comics[id].list
	list.each(function(item){ chids.push(item.chid); });
	params = {'id':id, 'chids[]':chids};
	Element.show('working' + id);
	Element.hide('workingerror'+id);
	new Ajax.Request(url_report, {
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
					Element.show('ok'+id);
					setTimeout("Element.hide('ok" + id + "')", 5000);
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

function removecomic(id) {
	if(unreadComics[id]) {
		markread(id, 0);
	}
	var params = {'id':id}
	Element.show('working' + id);
	new Ajax.Request(url_remove, {
		method: 'post',
		parameters: params,
		onSuccess: function(transport) {
			if (transport.status == 0) {
				//Error
				Element.hide('working'+id);
				Element.show('workingerror'+id);
				console.log("Error removing comic: no status 200");
			} else if (transport.status == 200) {
				//quitar el comic de la principal
				cdiv = $('c'+id);
				//siguiente div hermano
				mover_a = cdiv.next();
				//buscamos uno que sea visible ahora mismo
				while(mover_a != null && !mover_a.visible()) {
					mover_a = mover_a.next();
				}
				if (mover_a == null) {
					//no hay siguiente, pues anterior
					mover_a = cdiv.previous();
					//buscamos uno que sea visible ahora mismo
					while(mover_a != null && !mover_a.visible()) {
						mover_a = mover_a.previous();
					}
				}
				//ocultar el div y quitarlo del dom
				cdiv.hide();
				cdiv.remove();
				//quitarlo de las listas
				comics[id] = null;
				//no quedan comics en la lista, mostrar aviso
				if ($('comics').childElements().length == 0) {
					$('noComicsSelected').show();
				}
				else {
					mover_a.scrollToExtra(-40);
				}
				//actualizar contadores
				comicCounter -= 1;
				updateCounters();
			}
		},
		onFailure: function(transport) {
			//Error
			Element.hide('working'+id);
			Element.show('workingerror'+id);
			console.log("Error removing comic: failure");
		},
		onException: function(req, exc) {
			//Error
			Element.hide('working'+id);
			Element.show('workingerror'+id);
			console.log("Error removing comic: exception: " + exc);
		}
	});
}
function mark_all_read(){
	$("mark_all_read_anim").show();
	new Ajax.Request(url_mark_all_read, {
		onSuccess: function() {
			$("mark_all_read_anim").hide();
			//update counters and arrays
			unreadCounter = 0;
			updateCounters();
			for(var i = 0;i < unreadComics.length; i++){ unreadComics[i] = false; }
			//now we hide every comic
			showUnreadComics();
			//hide link to mark all read
			$("mark_all_read").hide();
		},
		onFailure: function() {
			$("mark_all_read_anim").hide();
		}
	});
}