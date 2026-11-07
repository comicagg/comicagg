/*jslint white: true, onevar: true, undef: true, nomen: false, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, newcap: true, immed: true, strict: true */
/*global startRequest, removeComicId, url_save_selection, url_remove_list, usercomics: true, dojo, setTimeout, updateCounters, byId, showElement, hideElement */
"use strict";
function save() {
    var params, items, ids, i, len;
    items = byId('user_comics').querySelectorAll('.dojoDndItem');
    ids = items.length > 0 ? items[0].getAttribute('comicid') : "";
    for (i = 1, len = items.length; i < len; i = i + 1) {
        ids += "," + items[i].getAttribute('comicid');
    }
    showElement(byId('saving_text'));
    hideElement(byId('save_error'));
    hideElement(byId('saved'));
    params = {'selected': ids};
    startRequest(url_save_selection, {
        method: 'post',
        parameters: params,
        onSuccess: function (counters) {
            showElement(byId('saved'));
            hideElement(byId('saving_text'));
            setTimeout(
                function () {
                    hideElement(byId('saved'));
                }, 6000);
            updateCounters(counters);
        },
        onFailure: function () {
            hideElement(byId('saved'));
            showElement(byId('save_error'));
            hideElement(byId('saving_text'));
        }
    });
}
//convierte la lista de objetos newcomics a una lista de elementos span
function convertNodes() {
    var nodes, i, len, c, e;
    nodes = [];
    for (i = 0, len = usercomics.length; i < len; i = i + 1) {
        c = usercomics[i];
        e = document.createElement('span');
        e.setAttribute('comicid', c.id);
        e.innerHTML = c.name;
        nodes[i] = e;
    }
    return nodes;
}
var dojo_usercomics;
function initDND() {
    var trash;
    dojo_usercomics = new dojo.dnd.Source("user_comics", {
        horizontal: true
    });
    //save the list when comics are moved within the list
    dojo.connect(dojo_usercomics, "onDropInternal", function (nodes, copy) {
        save();
    });
    //insert nodes in dojo dnd
    dojo_usercomics.insertNodes(false, convertNodes());
    //init the trash
    trash = new dojo.dnd.Target("trash");
    //do something when comics are dropped in the trash
    dojo.connect(trash, "onDropExternal", function (source, nodes, copy) {
        var ids, i, params;
        showElement(byId('saving_text'));
        hideElement(byId('save_error'));
        hideElement(byId('saved'));
        trash.selectAll();
        trash.deleteSelectedNodes();
        trash.clearItems();
        ids = nodes[0].getAttribute('comicid');
        for (i = 1; i < nodes.length; i = i + 1) {
            ids += "," + nodes[i].getAttribute('comicid');
        }
        params = { 'ids': ids };
        startRequest(url_remove_list, {
            method: 'post',
            parameters: params,
            onSuccess: function (counters) {
                var i, id, removed;
                showElement(byId('saved'));
                hideElement(byId('saving_text'));
                setTimeout(
                    function () {
                        hideElement(byId('saved'));
                    }, 6000);
                removed = false;
                for (i = 0; i < nodes.length; i = i + 1) {
                    id = parseInt(nodes[i].getAttribute('comicid'), 10);
                    if (removeComicId(usercomics, id)) {
                        removed = true;
                    }
                }
                if (removed) {
                    usercomics = usercomics.filter(function (c) {
                        return c !== null && c !== undefined;
                    });
                }
                updateCounters(counters);
            },
            onFailure: function () {
                hideElement(byId('saved'));
                showElement(byId('save_error'));
                hideElement(byId('saving_text'));
            }
        });
    });
    //change the text that appears while dragging
    dojo.dnd.Avatar.prototype._generateText = function () {
        return (this.manager.nodes.length + " comic" +
            (this.manager.nodes.length !== 1 ? "s" : ""));
    };
}

function setNewList(is) {
    dojo_usercomics.selectAll();
    dojo_usercomics.deleteSelectedNodes();
    dojo_usercomics.clearItems();
    dojo_usercomics.insertNodes(false, is);
}
function etoString(e) {
    var s = e.name;
    s += " " + e.score + "%";
    s += " " + e.total_votes + "v";
    return s.toLowerCase();
}
function sort_az(a, b) {
    a = etoString(a);
    b = etoString(b);
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
function sort_score(a, b) {
    var x, y, ret;
    x = parseInt(a.score, 10);
    y = parseInt(b.score, 10);
    ret = y - x;
    if (ret === 0) {
        x = parseInt(a.total_votes, 10);
        y = parseInt(b.total_votes, 10);
        ret = y - x;
        if (ret === 0) {
            ret = sort_az(a, b);
        }
    }
    return ret;
}
function sort_items(az) {
    if (az) {
        usercomics.sort(sort_az);
    } else {
        usercomics.sort(sort_score);
    }
    setNewList(convertNodes());
    save();
}
