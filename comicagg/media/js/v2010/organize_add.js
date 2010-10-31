function onclick_url(event) {
    event.stop();
    openurl($("comic_url").href);
}
var comics;
function initAdd() {
    comics = $('add').select('.comic');
    for (var i=0, len=comics.length; i < len; i++) {
        var comic = comics[i];
        var id = comic.id.substring(6);
        if(containsComicId(usercomics, id)) {
            comic.addClassName('added');
        } else if(containsComicId(availablecomics_new, id)) {
            comic.addClassName('new');
        }
        comic.observe('click', onClickComic);
        comic.observe('mouseover', onMouseOverComic);
        comic.observe('mouseout', onMouseOutComic);
    }
    $("comic_url").observe("click", onclick_url);
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
    elem.addClassName('working');
    elem.removeClassName('error');
    if(comic = containsComicId(usercomics, id)) {
        //comic is selected, remove it! TODO
        var params = {'id': id};
        new Ajax.Request(url_remove, {
            method: 'post',
            parameters: params,
            onSuccess: function(response) {
                if (response.status = 200) {
                    elem.removeClassName('added');
                    //remove it from the users comic list
                    if (removeComicId(usercomics, id)) {
                        usercomics = usercomics.compact();
                    }
                } else {
                    elem.addClassName('error');
                }
                elem.removeClassName('working');
            },
            onFailure: function(response) {
                elem.addClassName('error');
                elem.removeClassName('working');
            }
        });
    }
    else {
        //comic is not selected, add it!
        comic = containsComicId(availablecomics, id);
        var params = {'id': id};
        new Ajax.Request(url_add, {
            method: 'post',
            parameters: params,
            onSuccess: function(response) {
                if (response.status = 200) {
                    elem.removeClassName('new');
                    elem.addClassName('added');
                    //remove it from the new comics list
                    if (removeComicId(availablecomics_new, id)) {
                        availablecomics_new = availablecomics_new.compact();
                    }
                    //add it to the user comics list
                    usercomics.push(comic);
                } else {
                    elem.addClassName('error');
                }
                elem.removeClassName('working');
            },
            onFailure: function(response) {
                elem.addClassName('error');
                elem.removeClassName('working');
            }
        });
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
    if (comic = containsComicId(availablecomics_new, id)) {
        //es un comic nuevo
        $('comic_new').show();
        //forget as new comic
        new Ajax.Request(comic.url_forget, {
            onSuccess: function(response) {
                if (response.status = 200) {
                    //remove green label
                    $('comic_' + id).removeClassName("new");
                    //update the counter in the menu
                    if(parseInt(response.responseText) == 0) {
                        $('menuNewComicCounter').innerHTML = "";
                    } else {
                        $('menuNewComicCounter').innerHTML = " (" + response.responseText + ")";
                    }
                    //remove it from the new comic list
                    if (removeComicId(availablecomics_new, currentid)) {
                        available_new = available_new.compact();
                    }
                }
            }
        });
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
    for(i = 0, len = comics.length; i < len; i++) {
        var comic = comics[i];
        txt = comic.innerHTML.toLowerCase();
        classes = comic.className.split(" ");
        for (j = 0; j < classes.length; j++) {
            if (classes[j].length > 0) {
                txt += " @" + classes[j];
            }
        }
        if(l > 0 && txt.indexOf(v) < 0) {
            comic.hide();
        } else {
            comic.show();
        }
    }
}
function filter_allcomics() {
    $("filterReal").value = "";
    switchFilter(true);
    filter("");
}
function filter_newcomics() {
    $("filterReal").value = "@new";
    switchFilter(false);
    filter("@new");
}
function filter_addedcomics() {
    $("filterReal").value = "@added";
    switchFilter(false);
    filter("@added");
}
