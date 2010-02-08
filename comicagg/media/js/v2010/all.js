function focusOnLogin() {
  $('id_username').focus();
}

// Configure

function saveSort() {
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
function initAdd() {
	var comics = $('add').select('.comic');
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
function onMouseOverComic(event){
	var elem = event.element();
	var id = elem.id.substring(6);
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
	$('comic_url').href = comic.url;
	if(comic.noimages) {
		$('noimages').show();
	} else {
		$('noimages').hide();
	}
}
function onMouseOutComic(event){
	var elem = event.element();
	var id = elem.id.substring(6);
}
