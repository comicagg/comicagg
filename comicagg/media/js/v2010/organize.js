// Configure

function save() {
	var ids = "";
	for (var i = 0, len = newcomics.length; i < len; i++) {
		ids += newcomics[i].id;
		if (i < len - 1) { ids += ","; }
	}
	var idsr = "";
	for (var i = 0, len = removedcomics.length; i < len; i++) {
		idsr += removedcomics[i].id;
		if (i < len - 1) { idsr += ","; }
	}	
	$('save_error').hide();
	$('save_text').hide();
	$('saving_text').show();
	$('saved_ok').hide();
	var params = {'selected': ids, 'removed':idsr};
	tmp = params;
	new Ajax.Request(url_save_selection, {
		method: 'post',
		parameters: params,
		onSuccess: function(response) {
			if (response.status = 200) {
				$('save_text').show();
				$('saved_ok').show();
				$('saving_text').hide();
				$('save_error').hide();
				usercomics = newcomics.clone();
				var i = setTimeout(function(){$('saved_ok').hide();}, 6000);
			} else {
				$('save_text').show();
				$('save_error').show();
				$('saving_text').hide();
				$('saved_ok').hide();
			}
		},
		onFailure: function(response) {
			$('save_text').show();
			$('save_error').show();
			$('saving_text').hide();
			$('saved_ok').hide();
		}
	});
}
function revert() {
	newcomics = usercomics.clone();
	setNewList(convertNodes());
}
function sort_items(az) {
	if (az) { newcomics.sort(_sort_az); }
	else { newcomics.sort(_sort_score); }
	setNewList(convertNodes());
}
function setNewList(is){
	dojo_usercomics.selectAll();
	dojo_usercomics.deleteSelectedNodes();
	dojo_usercomics.clearItems();
	dojo_usercomics.insertNodes(false, is);
}
function _sort_score(a, b) {
	x = parseInt(a.score);
	y = parseInt(b.score);
	ret = y - x;
	if (ret == 0) {
		x = parseInt(a.votes);
		y = parseInt(b.votes);
		ret = y - x;
		if (ret == 0) {
			ret = _sort_az(a,b);
		}
	}
	return ret;
}
function _sort_az(a, b) {
	a = etoString($(a));
	b = etoString($(b));
	if (a > b) {
		return 1;
	}
	else if (a < b) {
		return -1;
	}
	else {
		return 0;
	}
}
function etoString(e) {
	var s = e.name;
	s += " " + e.score + "%";
	s += " " + e.votes + "v";
//   n = elem.select('.new_comic')[0];
//   if(n) { s += " @new"; }
	return s.toLowerCase();
}

//borrar esta variable
var tmp;

var dojo_usercomics;

//convierte la lista de objetos newcomics a una lista de elementos span
function convertNodes() {
	var nodes = new Array();
	for (var i = 0, len = newcomics.length; i < len; i++) {
		c = newcomics[i];
		e = new Element('span', {'comicid':c.id});
		e.innerHTML = c.name;
		nodes[i] = e;
	}
	return nodes;
}

//recibe una lista de nodosa borrar, saca el id del comic de cada nodo
//elimina los comic de la lista newcomics y compacta la lista
function dndRemoveComics(nodes) {
	var tmp = new Array();
	for (var i = 0; i < nodes.length; i++) {
		tmp[i] = parseInt(nodes[i].getAttribute('comicid'));
	}
	for (var i = 0, len = newcomics.length; i < len; i++) {
		if (tmp.indexOf(newcomics[i].id) > -1) {
			removedcomics.push(newcomics[i]);
			newcomics[i] = null;
		}
	}
	newcomics = newcomics.compact();
}
function initDND() {
	dojo_usercomics = new dojo.dnd.Source("user_comics", {
		horizontal:true,
	});
	//insert nodes in dojo dnd
	dojo_usercomics.insertNodes(false, convertNodes());
	
	var trash = new dojo.dnd.Target("trash");
	dojo.connect(trash, "onDropExternal", function(source, nodes, copy) {
		dndRemoveComics(nodes);
		trash.selectAll();
		trash.deleteSelectedNodes();
		trash.clearItems();
	});
	dojo.dnd.Avatar.prototype._generateText = function(){
		return (this.manager.nodes.length + " comic" +
			(this.manager.nodes.length != 1 ? "s" : ""));
	};
}
var comics;
function initAdd() {
	comics = $('add').select('.comic');
	for (var i=0, len=comics.length; i < len; i++) {
		var comic = comics[i];
		var id = comic.id.substring(6);
		if(containsComicId(usercomics, id)) {
			comic.addClassName('added');
		} else if(containsComicId(available_new, id)) {
			comic.addClassName('new');
		}
		comic.observe('click', onClickComic);
		comic.observe('mouseover', onMouseOverComic);
		comic.observe('mouseout', onMouseOutComic);
	}
}
function containsComicId(array, comicid) {
	var found = false;
	for (var i=0, len=array.length; i < len && !found; ++i) {
		comic = array[i];
		found = comic.id == comicid;
	}
	return found ? comic : found;
}
function removeComicId(array, comicid) {
	var found = false;
	for (var i=0, len=array.length; i < len && !found; i++) {
		comic = array[i];
		found = comic.id == comicid;
		if (found) {
			array[i] = undefined;
		}
	}
	return found ? comic : found;
}
function onClickComic(event) {
	var elem = event.element();
	var id = elem.id.substring(6);
	//comic is selected? deselect
	if(comic = containsComicId(newcomics, id)) {
		removeComicId(newcomics, id);
		newcomics = newcomics.compact();
		if (removeComicId(addedcomics, id)) {
			addedcomics = addedcomics.compact();
		}
		removedcomics.push(comic);
		elem.removeClassName('added');
	}
	//not selected? remove from newcomics
	else {
		comic = containsComicId(availablecomics, id);
		newcomics.push(comic);
		addedcomics.push(comic);
		elem.removeClassName('new');
		elem.addClassName('added');
		//quitarlo de available_new
		if (removeComicId(available_new, id)) {
			available_new = available_new.compact();
		}
		//quitarlo de removedcomics
		if (removeComicId(removedcomics, id)) {
			removedcomics = removedcomics.compact();
		}
	}
}
var lastevent;
var timerid;
function onMouseOverComic(event){
	lastevent = event;
	timerid = setTimeout("mouseOverAction()", 500);
}
var currentid = 0;
function mouseOverAction() {
	var elem = lastevent.element();
	var id = elem.id.substring(6);
	currentid = id;
	if (comic = containsComicId(available_new, id)) {
		//es un comic nuevo
		$('comic_new').show();
	} else if (comic = containsComicId(usercomics, id)) {
		//TODO deselect comic
		$('comic_new').hide();
	} else if (comic = containsComicId(availablecomics, id)) {
		//TODO select comic
		$('comic_new').hide();
	}
	$('comic_info_wrap').show();
	$('comic_name').innerHTML = comic.name;
	$('comic_score').innerHTML = comic.score;
	$('comic_votes').innerHTML = comic.votes;
	$('comic_updated').innerHTML = comic.updated;
	$('comic_readers').innerHTML = comic.readers;
	$('comic_url').href = comic.url;
	if(comic.noimages) {
		$('noimages').show();
		$('comic_last').hide();
	} else {
		$('noimages').hide();
		$('loading').show();
		$('comic_last').hide();
		img = new Image();
		img.src = comic.last;
		img.id = comic.id;
		img.onload = function() {
			if (currentid != this.id) { return 0; }
			$('loading').hide();
			$('comic_last').show();
			t = $('comic_last').cumulativeOffset()['top'];
			d = $('comic_info').getDimensions();
			di = $('comic_info').cumulativeOffset();
			r = this.width / this.height;
			maxw = $('comic_image').getDimensions()['width'];
			maxh = di['top'] + d['height'] - t - 10;
			$('comic_last').style.width = this.width + "px";
			$('comic_last').style.height = this.height + "px";
			w = this.width;
			h = this.height;
			if (r > 1) { //horiz
				if (w > maxw) {
					h = parseInt(maxw / r);
					$('comic_last').style.width = maxw + "px";
					$('comic_last').style.height = h + "px";
				}
				if (h > maxh) {
					w = parseInt(maxh * r);
					$('comic_last').style.width = w + "px";
					$('comic_last').style.height = maxh + "px";
				}
			} else {
				if (h > maxh) {
					w = parseInt(maxh * r);
					$('comic_last').style.width = w + "px";
					$('comic_last').style.height = maxh + "px";
				}
				if (w > maxw) {
					h = parseInt(maxw / r);
					$('comic_last').style.width = maxw + "px";
					$('comic_last').style.height = h + "px";
				}
			}
			$('comic_last').src = this.src;
		};
		img.onerror = function() {
			$('loading').hide();
			$('comic_last').show();
			$('comic_last').src = media_url + "images/broken32.png";
			$('comic_last').style.width = "32px";
			$('comic_last').style.height = "32px";
		}
	}
}
function onMouseOutComic(event) {
	clearTimeout(timerid);
}
function switchFilter(back) {
	if(back && $('filterReal').value.length == 0) {
		$('filter').show();
		$('filterReal').hide();
	} else {
		$('filter').hide();
		$('filterReal').show();
		$('filterReal').focus();
	}
}
var idFilter = -1;
function filter(v) {
	clearTimeout(idFilter);
	idFilter = setTimeout('applyFilter("'+ v +'")', 100);
}
function applyFilter(v){
	l = v.length;
	for(i=0, len=comics.length; i < len; i++) {
		var comic = comics[i];
		txt = comic.innerHTML.toLowerCase();
		if(l>0 && txt.indexOf(v) < 0) {
			comic.hide();
		} else {
			comic.show();
		}
	}
}