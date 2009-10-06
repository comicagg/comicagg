function updateCounters() {
	$('menuUnreadCounter').innerHTML = ' (' + unreadCounter + ')';
	$('infoUnreadCounter').innerHTML = unreadCounter;
	$('totalComicCounter').innerHTML = comicCounter;
}

function showAllComics() {
	clist = $$('.comic');
	for (i = 0; i < clist.length; i++) {
		clist[i].show();
	}
	$('showingAll').show();
	$('showingUnread').hide();
}

function showUnreadComics() {
	clist = $$('.comic');
	for (i = 0; i < clist.length; i++) {
		// TODO si tiene unread
		cid = clist[i].id.substring(1);
		console.log(cid);
		if (!unreadComics[cid]) {
			clist[i].hide();
		}
	}
	$('showingAll').hide();
	$('showingUnread').show();
}
