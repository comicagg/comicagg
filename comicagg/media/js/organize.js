// Configure
function save_organize() {
    items = $('user_comics').select('.dojoDndItem');
    items_o = new Array();
    for (var i = 0, len = items.length; i < len; i++) {
        id = items[i].getAttribute('comicid');
        items_o.push(usercomics_id[id]);
    }
    newcomics = items_o;
    save();
}

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

//recibe una lista de nodos a borrar, saca el id del comic de cada nodo
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
    //iniciar la papelera
    var trash = new dojo.dnd.Target("trash");
    dojo.connect(trash, "onDropExternal", function(source, nodes, copy) {
        dndRemoveComics(nodes);
        trash.selectAll();
        trash.deleteSelectedNodes();
        trash.clearItems();
    });
    //texto que sale al arrastrar
    dojo.dnd.Avatar.prototype._generateText = function(){
        return (this.manager.nodes.length + " comic" +
            (this.manager.nodes.length != 1 ? "s" : ""));
    };
}
