function focusOnLogin() {
  $('id_username').focus();
}

// Configure

function saveSort() {
	var items = $$('.item');
	var noitems = items.length;
	var ids = "";
	for (i=0; i < noitems; i++) {
		ids += items[i].id;
		if (i != noitems - 1) { ids += ","; }
	}
	$('save_error').hide();
	$('save_text').hide();
	$('saving_text').show();
	$('saved_ok').hide();
	var params = {'selected_list[]': ids}
	new Ajax.Request(url_save_selection, {
		method: 'post',
		parameters: params,
		on200: function(response) {
			$('save_text').show();
			$('saved_ok').show();
			$('saving_text').hide();
			$('save_error').hide();
			var i = setTimeout(function(){$('saved_ok').hide();}, 6000);
		},
		on0: function(response) {
			$('save_text').show();
			$('save_error').show();
			$('saving_text').hide();
			$('saved_ok').hide();
		},
		onException: function(response) {
			$('save_text').show();
			$('save_error').show();
			$('saving_text').hide();
			$('saved_ok').hide();
		}
	});
}
