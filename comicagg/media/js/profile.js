function change_color(new_color)
{
  if(current_color == new_color) { return false; }
  switch(new_color) {
    case "green_white":
        var url = css_green_white;
    break;
    case "gray_white":
        var url = css_gray_white;
    break;
    case "red_white":
        var url = css_red_white;
    break;
    default:
        var url = css_blue_white;
  }
  $('css_file').href = url;
  current_color = new_color;
  save_color(new_color);
}

function save_color(new_color) {
  var url = url_save_color;
  Element.show('working');
  var params = {'new_color':new_color}
  new Ajax.Request(url, {
    method: 'post',
    parameters: params,
    onSuccess: function(response) {
      Element.hide('working');
    },
    onFailure: function(response) { }
  });
}