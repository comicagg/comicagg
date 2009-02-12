// **************
// configure page init function
// **************

filtering = false;

function initConfigure() {
	if($('show_new')) {
		$('show_new').onclick = function() {
			$('filter_input_available').value = '@new';
			filter_list($('filter_input_available'), 'available_list');
		};
	}
	//setup filters
	$('filter_input_available').onkeyup = function() { filter_list($('filter_input_available'), 'available_list'); };
	$('clear_available').onclick = function() { filter_clear('filter_input_available', 'available_list'); };
	$('filter_input_selected').onkeyup = function() { filter_list($('filter_input_selected'), 'selected_list'); };
	$('clear_selected').onclick = function() { filter_clear('filter_input_selected', 'selected_list'); };
	//setup side options
	$('sort_az').onclick = function() { sort_selected('az'); };
	$('sort_rating').onclick = function() { sort_selected('rating'); };
	$('add_all').onclick = function() { add_all(); };
	$('remove_all').onclick = function() { remove_all(); };
	$('sort_available').onclick = function() { sort_available(); };
  //setup items
/*  var es = $$('.sortable_box .item');
  for(var i=0; i < es.length; i++) {
    es[i].onmouseover = function(event) {
      id = parseInt(event.target.id.substring(2));
      Element.show('info' + id);
    };
    es[i].onmouseout = function(event) {
      id = parseInt(event.target.id.substring(2));
      infoHide(id);
    };
  }*/
	var es = $$('.comic_info');
	for(var i=0; i < es.length; i++) {
		es[i].onclick = function(event) { id = parseInt(event.target.parentNode.id.substring(4)); menuToggle(id); };
	}
	var es = $$('.desc');
	for(var i=0; i < es.length; i++) {
		es[i].onclick = function(event) { id = parseInt(event.target.parentNode.id.substring(4)); gotoDescription(id); };
	}
	var es = $$('.desc_img');
	for(var i=0; i < es.length; i++) {
		es[i].onclick = function(event) { id = parseInt(event.target.parentNode.parentNode.id.substring(4)); gotoDescription(id); };
	}
	var es = $$('.add');
	for(var i=0; i < es.length; i++) {
		es[i].onclick = function(event) { id = parseInt(event.target.parentNode.id.substring(4)); addComic(id); };
	}
	var es = $$('.add_img');
	for(var i=0; i < es.length; i++) {
		es[i].onclick = function(event) { id = parseInt(event.target.parentNode.parentNode.id.substring(4)); addComic(id); };
	}
	var es = $$('.remove');
	for(var i=0; i < es.length; i++) {
		es[i].onclick = function(event) { id = parseInt(event.target.parentNode.id.substring(4)); removeComic(id); };
	}
	var es = $$('.remove_img');
	for(var i=0; i < es.length; i++) {
		es[i].onclick = function(event) { id = parseInt(event.target.parentNode.parentNode.id.substring(4)); removeComic(id); };
	}

	Sortable.create("available_list", {
		dropOnEmpty:true,
		containment:["available_list","selected_list"],
		constraint:false,
		scroll: window,
		only: "item"
	});
	
	Sortable.create("selected_list", {
		dropOnEmpty:true,
		containment:["available_list","selected_list"],
		constraint:false,
		scroll: window,
		only: "item",
		onUpdate:function(elem) {
		do_save();
		sort_available();
		}
	});
	ajustar_alturas(true);
	$('sortables_loading').hide();
	$('sortables_wrap').show();
	return true;
}

// **************
// functions
// **************

// id del elemento actual mostrado
var currentMenu = -1;
// true if the menu was just activated. prevents hide on event bubbling
var activated = false;

function processClick()
{
  if (!activated && currentMenu > 0) {
    Element.hide('info'+currentMenu);
    menuToggle(currentMenu);
    currentMenu = -1;
  }
  activated = false;
}

function infoHide(id)
{
  //  si el elemento actual es distinto del menu activo, ocultar info actual
  if (currentMenu != id) {
    Element.hide('info'+id);
  }
}

function menuToggle(id)
{
  if (currentMenu > 0) {
    //  hay un menú activo distinto del actual, desactivarlo y activar el nuevo
    if (currentMenu != id) {
      $('menu_image'+currentMenu).src = media_url + 'images/configure.png';
      Element.hide('menu'+currentMenu);
      Element.hide('info'+currentMenu);
      $('menu_image'+id).src = media_url + 'images/configure_on.png';
      Element.show('menu'+id);
      currentMenu = id;
      activated = true;
    }
    //  hay un menu activo y es el actual, desactivarlo
    else {
      Element.hide('menu'+currentMenu);
      $('menu_image'+currentMenu).src = media_url + 'images/configure.png';
//       Element.hide('info'+currentMenu);
      currentMenu = -1;
      activated = true;
    }
  } else {
    // no hay menu activo, activar actual
    Element.show('menu'+id);
    $('menu_image'+id).src = media_url + 'images/configure_on.png';
    currentMenu = id;
    activated = true;
  }
}

function sort_selected(kind)
{
  Element.show('working');
  var nodes = $('selected_list').select('.item');
  for(var i=0; i < nodes.length; i++)
  {
    var item = nodes[i];
    $('selected_list').removeChild(item);
  }
  if (kind == 'az') {
    nodes.sort(sort_az);
  } else if (kind == 'rating') {
    nodes.sort(sort_rating);
  }
  for(var i=0; i < nodes.length; i++)
  {
    var item = nodes[i];
    $('selected_list').appendChild(item);
  }
  do_save();
}

function add_all()
{
  Element.show('working');
  var dest = $('selected_list')
  while($('available_list').firstChild)
  {
    node = $('available_list').firstChild;
    dest.appendChild(node);
  }
  do_save();
}

function remove_all()
{
  var dest = $('available_list')
  nodes = $('selected_list').select('.item');
  if (nodes.length > 0) {
    Element.show('working');
    for (var i = 0; i < nodes.length; i++)
    {
      node = nodes[i];
      dest.appendChild(node);
    }
    do_save();
//     sort_available();
  }
}

function do_save()
{
  Element.show('working');
  $('saved').innerHTML = '';
  nodes = $('selected_list').select('.item');
  if(nodes.length > 0)
  {
    $('drag_drop').hide();
  }
  else
  {
    $('drag_drop').show();
  }
  str = "";
  for (var i = 0; i < nodes.length; i++)
  {
    str += nodes[i].id;
    if (i!=nodes.length-1)
    {
      str += ",";
    }
    //actualizar menu
    nodes[i].select('.add')[0].hide();
    nodes[i].select('.remove')[0].show();
  }
  var url = url_save_selection;
  var params = {'selected_list[]': str}
  new Ajax.Request(url, {
    method: 'post',
    parameters: params,
    onSuccess: function(response) {
      ret = response.responseText;
      if (ret!=-1)
      {
        $('saved').innerHTML = ret;
        $('saved').show();
        $('available_list').style.height = "100%";
        $('selected_list').style.height = "100%";
        ajustar_alturas(false);
        Element.hide('working');
//         setTimeout("Effect.Fade('saved')", 15000)
      }

    },
    onFailure: function(response) {
//       ret = response.responseText;
//       document.write(ret);
    }
  });
//   $('save_button').disabled = false;
}

function sort_available()
{
/*  var t1 = new Date();
  str = t1.getMinutes() + " " + t1.getSeconds() + "." + t1.getMilliseconds() + "\n";*/
  var nodes = $('available_list').childElements();
  for(var i=0; i < nodes.length; ++i)
  {
    var item = nodes[i];
    $('available_list').removeChild(item);
  }
/*  t1 = new Date();
  str += t1.getMinutes() + " " + t1.getSeconds() + "." + t1.getMilliseconds() + "\n";*/
  nodes.sort(sort_az);
/*  t1 = new Date();
  str += t1.getMinutes() + " " + t1.getSeconds() + "." + t1.getMilliseconds() + "\n";*/
  for(var i=0; i < nodes.length; ++i)
  {
    var item = nodes[i];
    $('available_list').appendChild(item);
    //actualizar menu
    item.select('.add')[0].show();
    item.select('.remove')[0].hide();
  }
/*  t1 = new Date();
  str += t1.getMinutes() + " " + t1.getSeconds() + "." + t1.getMilliseconds() + "\n";
  alert(str);*/
}

function filter_clear(filter_input, list)
{
  $(filter_input).value = "";
  filter_list($(filter_input), list);
  filtering = false;
  ajustar_alturas(false);
}

function filter_list(elem, list)
{
  var txt = elem.value.toLowerCase();
  if (txt.length==0)
  {
//     return;
  }
  var nodes = $(list).select('.item');
  for(var i=0; i < nodes.length; i++)
  {
    var item = nodes[i];
    var name = etoString(item);
//     alert(txt + " " + name + " " + name.match(txt));
    if (name.indexOf(txt) == -1)
    {
      Element.hide(item);
    }
    else
    {
      Element.show(item);
    }
  }
  filtering = true;
}

function sort_rating(a, b)
{
  x = parseInt(a.select('.rating')[0].innerHTML);
  y = parseInt(b.select('.rating')[0].innerHTML);
  ret = y-x;
  if (ret == 0) {
    x = parseInt(a.select('.votes')[0].innerHTML);
    y = parseInt(b.select('.votes')[0].innerHTML);
    ret = y-x;
  }
  return ret;
}

function sort_az(a, b)
{
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

function etoString(elem)
{
  n = elem.select('span.name')[0];
  s = n.innerHTML;
  n = elem.select('span.rating')[0];
  s += " " + n.innerHTML + "%";
  n = elem.select('span.votes')[0];
  s += " " + n.innerHTML + "v";
  n = elem.select('span.new_comic')[0];
  if(n) { s += " @new"; }
  return s.toLowerCase();
}

function ajustar_alturas(available)
{
  var offset = 42;
  var available_list = $('available_list');
  var selected_list = $('selected_list');
  ava_h = available_list.getHeight() - offset;
  sel_h = selected_list.getHeight() - offset;
//   alert("ava:" + ava_h + " sel:" + sel_h);
  if (ava_h > sel_h)
  {
    selected_list.style.height = ava_h + "px";
    if(available) { available_list.style.height = ava_h + "px"; }
  }
  else
  {
    if (available) { available_list.style.height = sel_h + "px"; }
    selected_list.style.height = sel_h + "px";
  }
//   ava_h = available_list.getHeight() - offset;
//   sel_h = selected_list.getHeight() - offset;
//   alert("ava:" + ava_h + " sel:" + sel_h);
}

function gotoDescription(id)
{
  var url = url_comic_list + '#comic' + id;
  window.location = url;
}

// desde el menu contextual de cada comic
function addComic(id)
{
  if(!id){ return false; }
  //añadirlo a la lista
  var elem = $('comic_'+id);
  if (elem) {
    elem.remove();
    $('selected_list').appendChild(elem);
  }
  do_save();
  //actualizar menu
  $$('#comic_'+id+' .add')[0].hide();
  $$('#comic_'+id+' .remove')[0].show();
}

// desde el menu contextual de cada comic
function removeComic(id)
{
  if(!id){ return false; }
  //quitarlo de la lista
  var elem = $('comic_'+id);
  if (elem) {
    elem.remove();
    $('available_list').appendChild(elem);
  }
  do_save();
//   sort_available();
  //actualizar menu
  $$('#comic_'+id+' .remove')[0].hide();
  $$('#comic_'+id+' .add')[0].show();
}
