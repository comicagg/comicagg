// Configure
function save() {
    items = $('user_comics').select('.dojoDndItem');
    var ids = items[0].getAttribute('comicid');
    for (var i = 1, len = items.length; i < len; i++) {
        ids += "," + items[i].getAttribute('comicid');
    }
    $('saving_text').show();
    $('save_error').hide();
    $('saved').hide();
    var params = {'selected': ids};
    new Ajax.Request(url_save_selection, {
        method: 'post',
        parameters: params,
        onSuccess: function(response) {
            if (response.status == 200) {
                $('saved').show();
                $('saving_text').hide();
                var i = setTimeout(function(){$('saved').hide();}, 6000);
            } else {
                $('saved').hide();
                $('save_error').show();
                $('saving_text').hide();
            }
        },
        onFailure: function(response) {
            $('saved').hide();
            $('save_error').show();
            $('saving_text').hide();
        }
    });
}
function sort_items(az) {
    if (az) { newcomics.sort(_sort_az); }
    else { newcomics.sort(_sort_score); }
    setNewList(convertNodes());
    save();
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
    return s.toLowerCase();
}

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

function initDND() {
    dojo_usercomics = new dojo.dnd.Source("user_comics", {
        horizontal:true,
    });
    //save the list when comics are moved within the list
    dojo.connect(dojo_usercomics, "onDropInternal", function(nodes, copy) {
        save();
    });
    //insert nodes in dojo dnd
    dojo_usercomics.insertNodes(false, convertNodes());
    //init the trash
    var trash = new dojo.dnd.Target("trash");
    //do something when comics are dropped in the trash
    dojo.connect(trash, "onDropExternal", function(source, nodes, copy) {
        $('saving_text').show();
        $('save_error').hide();
        $('saved').hide();
        trash.selectAll();
        trash.deleteSelectedNodes();
        trash.clearItems();
        ids = nodes[0].getAttribute('comicid');
        for (var i = 1; i < nodes.length; i++) {
            ids += "," + nodes[i].getAttribute('comicid');
        }
        var params = {'ids': ids};
        new Ajax.Request(url_remove_list, {
            method: 'post',
            parameters: params,
            onSuccess: function(response) {
                if (response.status == 200) {
                    $('saved').show();
                    $('saving_text').hide();
                    var i = setTimeout(function(){$('saved').hide();}, 6000);
                } else {
                    $('saved').hide();
                    $('save_error').show();
                    $('saving_text').hide();
                }
            },
            onFailure: function(response) {
                $('saved').hide();
                $('save_error').show();
                $('saving_text').hide();
            }
        });
    });
    //change the text that appears while dragging
    dojo.dnd.Avatar.prototype._generateText = function(){
        return (this.manager.nodes.length + " comic" +
            (this.manager.nodes.length != 1 ? "s" : ""));
    };
}
