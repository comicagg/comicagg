function focusOnLogin() {
  $('id_username').focus();
}

function openurl(url) { window.open(url); return false; }

// **************
// blog
// **************

function forget_new_posts() {
  var url = url_forget_new_blogs;
  new Ajax.Request(url, {
    method: 'post',
    onSuccess: function(response) {},
    onFailure: function(response) {}
  });
}
