// **************
// read page init function
// **************

var last_event = false;

function initRead() {
  var es = $$('.mark_as_read');
  for(var i=0; i < es.length; i++) {
    es[i].onclick = function(event) { id = parseInt(event.target.id.substring(4)); mark_as_read(id); };
  }
  var es = $$('.tags_link');
  for(var i=0; i < es.length; i++) {
    es[i].onclick = function(event) { id = parseInt(event.target.parentNode.id.substring(4)); toggle_tagging(id); };
  }
  var es = $$('.ratedown');
  for(var i=0; i < es.length; i++) {
    es[i].onclick = function(event) {
      last_event = event;
      var target = event.target;
      if(target.nodeName.toLowerCase() == "img") {
        id = parseInt(event.target.parentNode.id.substring(8));
      } else {
        id = parseInt(event.target.id.substring(8));
      }
      rate(id, -1);
    };
  }
  var es = $$('.rateup');
  for(var i=0; i < es.length; i++) {
    es[i].onclick = function(event) {
      last_event = event;
      var target = event.target;
      if(target.nodeName.toLowerCase() == "img") {
        id = parseInt(event.target.parentNode.id.substring(6));
      } else {
        id = parseInt(event.target.id.substring(6));
      }
      rate(id, 1);
    };
  }
  var es = $$('.more');
  for(var i=0; i < es.length; i++) {
    es[i].onclick = function(event) { id = parseInt(event.target.id.substring(4)); menuToggle(id); };
  }
  var es = $$('.more_img');
  for(var i=0; i < es.length; i++) {
    es[i].onclick = function(event) { id = parseInt(event.target.id.substring(10)); menuToggle(id); };
  }
  var es = $$('.report');
  for(var i=0; i < es.length; i++) {
    es[i].onclick = function(event) { id = parseInt(event.target.parentNode.id.substring(4)); reportComic(id); };
  }
  var es = $$('.remove');
  for(var i=0; i < es.length; i++) {
    es[i].onclick = function(event) { id = parseInt(event.target.parentNode.id.substring(4)); removeComicLink(id); };
  }
  var es = $$('.up');
  for(var i=0; i < es.length; i++) {
    es[i].onclick = function(event) { $('head').scrollTo(); };
  }
  var es = $$('.reloadimgs');
  for(var i=0; i < es.length; i++) {
    es[i].onclick = function(event) { id = parseInt(event.target.id.substring(10)); reloadimgs(id); };
  }
	loadimages();
}

// **************
// read page functions
// **************

function loadimages() {
	_comics = lcomics.clone();
	while(_comics.length > 0) {
		while((comic = _comics.shift()) == null && _comics.length > 0);
		if (comic != null) { loadcomicimages(comic); }
	}
}

var max_concurrent = 10;
var actual_no = 0;

function loadcomicimages(comic) {
// comics con imagenes nuevas
	if(comic.list.length > 0) {
		for (i=0; i<comic.list.length; i++) {
			item = comic.list[i];
			window['item' + item.id] = item;
			loadimage('item' + item.id);
		}
	}
}

function loadimage(item_str) {
	if(max_concurrent <= actual_no) {
		setTimeout("loadimage('" + item_str + "')", 300);
	} else {
		actual_no += 1;
		item = window[item_str];
		loadimage2("img_unread" + item.id, item.cid, new Image(), item.url);
	}
}

function loadimage2(id, cid, img, url) {
	e = $(id);
	e.src = url_loading;
	if (comics_width == -1) {
		comics_width = $('comics').getWidth();
	}
	img.src = url;
	img.onload = function(){
		e = $(id);
		actual_no -= 1;
		w = img.width;
		if (w >= comics_width) {
			if (e) { e.style.width = "100%"; }
		}
		if (e) { e.src = url; }
	};
	img.onerror = function(){
		e = $(id);
		actual_no -= 1;
		e.src = url_error;
		acc = "#c_" + cid + " .opts_left";
		acc2 = acc + "_error";
		$$(acc)[0].hide();
		$$(acc2)[0].show();
	};
	img.onabort = function(){
		e = $(id);
		actual_no -= 1;
		e.src = url_error;
	};
}

// id del elemento actual mostrado
var currentMenu = -1;
// true if the menu was just activated. prevents hide on event bubbling
var activated = false;

function processClick() {
  if (!activated && currentMenu > 0) {
//     Element.hide('menu'+currentMenu);
    Effect.Fade('menu'+currentMenu, { duration:0.5 });
    menuToggle(currentMenu);
    currentMenu = -1;
  }
  activated = false;
}

function menuToggle(id) {
  if (currentMenu > 0) {
    //  hay un menú activo distinto del actual, desactivarlo y activar el nuevo
    if (currentMenu != id) {
      $('menu_image'+currentMenu).src = media_url + 'images/menu_off.png';
//       Element.hide('menu'+currentMenu);
      Effect.Fade('menu'+currentMenu, { duration:0.5 });
      $('menu_image'+id).src = media_url + 'images/menu_on.png';
//       Element.show('menu'+id);
      Effect.Appear('menu'+id, { duration:0.5 });
      currentMenu = id;
      activated = true;
    }
    //  hay un menu activo y es el actual, desactivarlo
    else {
//       Element.hide('menu'+currentMenu);
      Effect.Fade('menu'+currentMenu, { duration:0.5 });
      $('menu_image'+currentMenu).src = media_url + 'images/menu_off.png';
      currentMenu = -1;
      activated = true;
    }
  } else {
    // no hay menu activo, activar actual
//     Element.show('menu'+id);
    Effect.Appear('menu'+id, { duration:0.5 });
    $('menu_image'+id).src = media_url + 'images/menu_on.png';
    currentMenu = id;
    activated = true;
  }
}

function reportComic(id) {
  var url = url_report;
  Element.show('working'+id);
  var params = {'id':id}
  new Ajax.Request(url, {
    method: 'post',
    parameters: params,
    onSuccess: function(response) {
      Element.hide('working'+id);
      Element.show('tick'+id);
      setTimeout("Effect.Fade('tick"+id+"')", 10000)
    },
    onFailure: function(response) {
    }
  });
}

function removeComicLink(id) {
	if(unread_list[id]) {
		mark_as_read(id);
	}
	var url = url_remove;
	var params = {'id':id}
	new Ajax.Request(url, {
		method: 'post',
		parameters: params,
		onSuccess: function(response) {
			//quitarlo el comic de la principal
			e = $('c_'+id);
			mover_a = e.next();
			if (mover_a == null) {
				mover_a = e.previous();
			}
			e.hide();
			e.remove();
			//quitarlo de las columnas del menu
			e = $('nav_unread_li_' + id);
			if(e) { e.remove(); }
			e = $('nav_all_li_' + id);
			e.remove();
			//quitarlo de las listas
			unread_list[id] = false;
			read_list[id] = false;
			if ($('comics').childElements().length == 0) { $('no_comics').show(); }
			else { mover_a.scrollTo(); }
		},
		onFailure: function(response) {
		}
	});
}

function ir_a(id, hidden) {
	e = $('c_' + id);
	if (!e.visible()) {
		o = {
			"id":'img_read' + id,
			"img":new Image(),
			"url":comics[id].url,
			"cb":"$('c_" + id + "').scrollTo()",
		};
		loadimgobj(o);
	}
	e.show();
	e.scrollTo();
	e = $('no_unread_notice');
	if(e) {
		e.hide();
	}
}

function hide_new_comics() {
  var url = url_hide_new_comics;
  new Ajax.Request(url, {
    method: 'post',
    onSuccess: function(response) {
      Effect.toggle('new_comics_notice');
    },
    onFailure: function(response) {
    }
  });
}

function hide_new_blogs() {
  var url = url_hide_new_blogs;
  new Ajax.Request(url, {
    method: 'post',
    onSuccess: function(response) {
      Effect.toggle('new_blogs_notice');
    },
    onFailure: function(response) {
    }
  });
}

function updateTitle() {
  if(count>0) {
    document.title = title + ' (' + count + ')';
  } else {
    document.title = title;
  }
}

function updateNavCount() {
  if(count>0) {
    $('navcount').innerHTML = count;
    Element.show('navunread');
  } else {
    $('navcount').innerHTML = "";
    Element.hide('navunread');
  }
}

function mark_all() {
  Element.show('loading_img');
  for(var i=0; i < unread_list.length; i++)
  {
    var item = unread_list[i];
    if (item) { mark_as_read(item.substring(5)); }
  }
  Element.show('mark_all_tick');
  Element.hide('loading_img');
}

var jump_status = 'show_unread';

function show_all()
{
  Element.show('nav_all');
  Element.hide('nav_unread');
  jump_status = 'show_all';
  Element.hide('showing_unread');
  Element.show('showing_all');
}

function show_unread()
{
  Element.hide('nav_all');
  Element.show('nav_unread');
  jump_status = 'show_unread';
  Element.show('showing_unread');
  Element.hide('showing_all');
}

function rate(id, val)
{
  var url = url_rate;
  var params = {'id': id, 'value':val}
  new Ajax.Request(url, {
    method: 'post',
    parameters: params,
    onSuccess: function(transport) {
      mark_as_read(id);
      Element.hide('sel'+id);
    },
    onFailure: function(transport) {
      console.log("[CA] Got an error, dumping...")
      console.log(last_event);
      console.log(transport);
      console.log("[CA] EOD")
//       console.log(transport.request.parameters);
    }
  });
}

function mark_as_read(id)
{
  var url = url_mark_as_read;
  var params = {'id': id}
  new Ajax.Request(url, {
    method: 'post',
    parameters: params,
    onSuccess: function(response) {
      ret = response.responseText;
      if (ret==0)
      {
        Element.show('mark_'+id); //muestra tick
        Element.hide('nav_all_no_'+id); //oculta numero en barra navegacion
        Element.hide('nav_unread_no_'+id); //oculta numero en barra navegacion
        $('nav_all_no_'+id).parentNode.className = ""; //quita la negrita del nombre del comic en navegacion
        Element.hide('new_'+id);  //oculta cartel nuevo en titulo del comic
        Element.show('done_read'+id); //muestra cartel leido
        Element.hide('mark'+id); //oculta enlace para marcar como leido
        Element.hide('sel'+id); //oculta votacion
        read_list[id] = 'read_'+id; //añade el comic a la lista de leidos
        unread_list[id] = undefined; //quita el comic de la lista de no leidos
        balanceColumns(id); //quitar el comic de la lista sin leer
        count--; //restar el contador de comics sin leer
        updateTitle();
        updateNavCount();
        if(count<1) {
          Element.hide('mark_all');
        }
      }
      else
      {
//         $('read').innerHTML = response.responseText;
      }

    },
    onFailure: function(response) {
//       $('read').innerHTML = response.responseText;
    }
  });
}

function balanceColumns(remove_id) {
//   alert('max='+items_per_column);
//   alert($('nav_all'));
  li_to_remove = $('nav_unread_li_' + remove_id );
  column = li_to_remove.parentNode;
  //quitar el li a borrar
  column.removeChild(li_to_remove);
  balanceColumnsAux(column);
}

function balanceColumnsAux(column) {
  //si hay siguiente columna podemos robar
  if (column.nextSiblings().length > 0) {
    //siguiente columna
    next_column = column.nextSiblings()[0];
    //si hay elementos podemos robar
    if(next_column.childElements().length > 0) {
      //primer elemento de la siguiente columna
      li_to_steal = next_column.childElements()[0];
      //lo quitamos
      next_column.removeChild(li_to_steal);
      //lo metemos al final de nuestra columna
      column.appendChild(li_to_steal);
      balanceColumnsAux(next_column);
    }
  }
}

function toggle_tagging(id) {
  Element.toggle('tags_'+id);
  Element.toggle('showtags'+id);
  Element.toggle('hidetags'+id);
}

function save_tags(id) {
  Element.show('saving_tags_'+id);
  var url = url_save_tags;
  var tags = $('user_tags_'+id).value
      var params = {'id': id, 'tags':tags}
  new Ajax.Request(url, {
    method: 'post',
    parameters: params,
    onSuccess: function(response) {
      ret = response.responseText;
      $('tagging_'+id).innerHTML = ret;
      Element.show('saved_'+id);
      Element.show('tags_'+id);
      Element.hide('saving_tags_'+id);
    },
    onFailure: function(response) {
      $('tagging_'+id).innerHTML = response.responseText;
    }
  });
}

function reloadimgs(id) {
	list = comics[id].list;
	if(list.length > 0) {
		for (i=0; i<list.length; i++) {
			item = window['item'+list[i].id];
			actual_no += 1;
			url = item.url + '?' + (new Date()).getTime();
			loadimage2('img_unread'+item.id, item.cid, new Image(), url);
		}
	}
}

function hidereloading(id) { if (actual_no == 0) { $('reloading' + id).hide(); } }