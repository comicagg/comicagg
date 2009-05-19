var loaded = Array();
var shown = Array();

function init() {
	var list = $$('.comic');
	for(var i=0; i < list.length; i++) {
		var comic = list[i];
		var span = comic.firstChild;
		span.onclick = function(event) {
			id = parseInt(event.target.parentNode.parentNode.id.substring(5));
			if (!(id > 0)) { id = parseInt(event.target.parentNode.id.substring(5)); }
			alternatecomic(id);
		};
	}
}

function alternatecomic(id) {
	if (id > 0) {
		var mon = $('menuon'+id);
		var moff = $('menuoff'+id);
		var holder = $('holder'+id);
		if (!(loaded[id])) {
			loaded[id] = true;
			//el comic no ha sido cargado, cargarlo y mostrarlo
			moff.hide();
			//cargar el comic
			loadcomic(id);
			return 0;
		}
/*		else {
			//el comic ya ha sido cargado
			if(shown[id]) {
			console.log("ocultar");
				//ocultar el comic
				moff.show();
				mon.hide();
				holder.hide();
				shown[id] = false;
				return 0;
			} else {
			console.log("mostrar");
				//mostrar el comic
				moff.hide();
				mon.show();
				holder.show();
				shown[id] = true;
				return 0;
			}
		}*/
	}
}

function loadcomic(id) {
	var load = $('loading' + id);
	var mon = $('menuon'+id);
	var moff = $('menuoff'+id);
	var comic = $('comic'+id);
	var error = $('error'+id);
	load.show();
	var url = url_comic_list_load;
	var params = {'id':id}
	new Ajax.Request(url, {
		method: 'post',
		parameters: params,
		onSuccess: function(transport) {
			_transport = transport;
// 			comic.appendChild(transport.responseXML.firstChild);
			shown[id] = true;
			load.hide();
			moff.hide();
			error.hide();
			mon.show();
			comic.innerHTML += transport.responseText;
		},
		onFailure: function(transport) {
// 			document.write(transport.responseText);
			loaded[id] = false;
			var load = $('loading' + id);
			var mon = $('menuon'+id);
			var moff = $('menuoff'+id);
			var comic = $('comic'+id);
			var error = $('error'+id);
			load.hide();
			mon.hide();
			moff.show();
			error.show();
		}
	});
	return 0;
}
