var comics_width = -1;
/* id elemento img, objeto img donde precargar imagen, url de la imagen */
function loadimg(id, img, url) {
	if (comics_width == -1) {
		comics_width = $('comics').getWidth();
	}
	img.src = url;
	img.onload = function(){
		e = $(id);
		w = img.width;
		if (w >= comics_width && e) { e.style.width = "100%"; }
		if (e) { e.src = url; }
	};
	img.onerror = function(){ $(id).src = url_error; };
	img.onabort = function(){ $(id).src = url_error; };
}

function loadimgobj(obj) {
	if (comics_width == -1) {
		comics_width = $('comics').getWidth();
	}
	img = new Image();
	img.src = obj.url;
	img.onload = function(){
		e = $(obj.id);
		w = img.width;
		if (w >= comics_width && e) { e.style.width = "100%"; }
		if (e) { e.src = obj.url; }
		if(obj.cb) { eval(obj.cb); }
	};
	img.onerror = function(){
		$(obj.id).src = url_error;
		if(obj.cb) { eval(obj.cb); }
	};
	img.onabort = function(){
		$(obj.id).src = url_error;
		if(obj.cb) { eval(obj.cb); }
	};
}

// **************
// comic list
// **************

function show_last(id, tmp, url) {
  Element.show('last' + id);
  Element.show('hidelast' + id);
  Element.hide('showlast' + id);
  loadimg('last' + id, tmp, url);
}

function hide_last(id) {
  Element.hide('last' + id);
  Element.hide('hidelast' + id);
  Element.show('showlast' + id);
}

function addcomic(id) {
  var url = url_add;
  Element.show('working'+id);
  var params = {'id':id}
  new Ajax.Request(url, {
    method: 'post',
    parameters: params,
    onSuccess: function(response) {
      Element.hide('working'+id);
      Element.hide('notreading'+id);
      Element.show('reading'+id);
    },
    onFailure: function(response) {
    }
  });
}

function removecomic(id) {
  var url = url_remove;
  Element.show('working'+id);
  var params = {'id':id}
  new Ajax.Request(url, {
    method: 'post',
    parameters: params,
    onSuccess: function(response) {
      Element.hide('working'+id);
      Element.hide('reading'+id);
      Element.show('notreading'+id);
    },
    onFailure: function(response) {
    }
  });
}

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


// **************
// other pages
// **************

function focusOnLogin()
{
  $('id_username').focus();
}

function check_register(the_form)
{
  valid = true;
  Element.hide('errorContainer');
  Element.hide('usernameNotValid');
  Element.hide('passwordsDontMatch');
  Element.hide('passwordBlank');
  Element.hide('emailError');
  Element.hide('captchaError');
  $('username_label').style.backgroundColor = 'transparent';
  $('password_label').style.backgroundColor = 'transparent';
  $('password2_label').style.backgroundColor = 'transparent';
  $('email_label').style.backgroundColor = 'transparent';
  $('captcha_label').style.backgroundColor = 'transparent';
  user = the_form.username.value;
  pass = the_form.password.value;
  pass2 = the_form.password2.value;
  email = the_form.email.value;
  captcha = the_form.captcha.value;

  if (captcha.length < 1)
  {
    Element.show('captchaError');
    $('captcha_label').style.backgroundColor = '#FFDBDB';
    valid = false;
  }
  if (user.match('[^a-zA-Z0-9_]') != null)
  {
    Element.show('usernameNotValid');
    $('username_label').style.backgroundColor = '#FFDBDB';
    valid = false;
  }
  if (user.length > 30 || user.length < 1)
  {
    Element.show('usernameNotValid');
    $('username_label').style.backgroundColor = '#FFDBDB';
    valid = false;
  }
  if (pass.length != pass2.length || pass != pass2)
  {
    Element.show('passwordsDontMatch');
    $('password_label').style.backgroundColor = '#FFDBDB';
    $('password2_label').style.backgroundColor = '#FFDBDB';
    valid = false;
  }
  if (pass.length + pass2.length == 0)
  {
    Element.show('passwordBlank');
    $('password_label').style.backgroundColor = '#FFDBDB';
    $('password2_label').style.backgroundColor = '#FFDBDB';
    valid = false;
  }
  if (email.match('.+@.+\..+') == null)
  {
    Element.show('emailError');
    $('email_label').style.backgroundColor = '#FFDBDB';
    valid = false;
  }
  if (!valid)
  {
    Element.show('errorContainer');
  }
  return valid;
}

function abrirWeb(url) { window.open(url); return false; }
