$(function() {
  function makeCurlCommand() {
    var f = $('form[method="post"]');
    var url = $('input[name="url"]').val();
    var callback_url = $('input[name="callback_url"]').val();
    var number = parseInt($('input[name="number"]').val(), 10);
    var post_files = !!($('input[name="post_files"]:checked').val() || false);
    var post_files_individually = !!($('input[name="post_files_individually"]:checked').val() || false);
    var download = !!($('input[name="download"]:checked').val() || false);
    var action = f.attr('action');
    if (action.indexOf('://') <= -1) {
      action = document.location.protocol + '//' + document.location.hostname +
      action;
    }
    var command = 'curl -v -X POST ';
    if (url.indexOf('&') > -1) {
      command += '--data-urlencode ';
    } else {
      command += '-d ';
    }
    command += 'url="' + url + '" \\\n';
    if (callback_url.indexOf('&') > -1) {
      command += '--data-urlencode ';
    } else {
      command += '-d ';
    }
    command += 'callback_url="' + callback_url + '" \\\n';
    command += '-d number=' + number + ' ';
    if (post_files) {
      command += '-d post_files=1 ';
      if (post_files_individually) {
        command += '-d post_files_individually=1 ';
      }
    }
    if (download) {
      command += '-d download=1 ';
    }
    // lastly
    command += ' \\\n' + action;
    $('#curl pre').html(command);
  }

  $('button.curl').on('click', function() {
    $('#curl').toggle();
    makeCurlCommand();
  });

  $('form input').on('input', function() {
    if ($('#curl:visible').length) makeCurlCommand();
  }).on('change', function() {
    if ($('#curl:visible').length) makeCurlCommand();
  });

});
