$(document).ready(function () {
    //toggleDetailEdit(unsaved);
});

function toggleDetailEdit(enable = true) {
    // set the detail fields to editable
    // show the notes box
    if (enable) {
        // enter edit mode
        console.log("enabling editor");
        // show the Save button
        $('#save').removeClass('disabled');
        $('#save').show();
        $('#btn-toggle-edit').addClass('btn-warning');
        $('#btn-toggle-edit').attr("onclick", "toggleDetailEdit(false)");
        // TODO: change the button's label to read "Stop Editing"
        $('.detail-control').addClass('unlocked');
        $('.detail-control').prop('disabled', false);
        //$('.extext-control').addClass('unlocked');
        //$('.extext-control').prop('disabled', false);
    } else {
        // exit edit mode
        $('#btn-toggle-edit').attr("onclick", "toggleDetailEdit(true)");
        // hide the Save button
        $('#save').addClass('disabled');
        $('#save').hide();
        $('#btn-toggle-edit').removeClass('btn-warning');
        $('.detail-control').removeClass('unlocked');
        $('.detail-control').prop('disabled', true);
        //$('.extext-control').removeClass('unlocked');
        //$('.extext-control').prop('disabled', true);
        //console.log("Has disabled class been added to controls?");
        //console.log($('.detail-control').hasClass('disabled'));

    }
}

// Save notes on submit
$('#qa-notes-form').on('submit', function (event) {
    event.preventDefault();
    console.log('submitting qa notes form')
    console.log(
        $('#qa-notes-textarea').val()
    )
    save_qa_notes();
});


// AJAX for posting
function save_qa_notes() {
    console.log("save_qa_notes is running")
    $.ajax({
        url: $('#qa-notes-form').attr("action"), // the endpoint
        type: "POST", // http method
        data: {
            qa_note_text: $('#qa-notes-textarea').val(),
        }, // data sent with the post request

        // handle a successful response
        success: function (json) {
            console.log(json); // log the returned json to the console
        },

        // handle a non-successful response
        error: function (xhr, errmsg, err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: " + errmsg +
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
};

// Todo: This function now contained within csrf_ajax.
// This code could be replaced with `import csrf_ajax from '../modules/csrf_ajax.js'`
$(function () {


    // This function gets cookie with a given name
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    var csrftoken = getCookie('csrftoken');

    /*
    The functions below will create a header with csrftoken
    */

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

});
// end csrf_ajax.js code

$('#chemical-audit-log-modal').on('show.bs.modal', function (event) {
    $('[data-toggle]').tooltip('hide');
    var modal = $(this);
    $.ajax({
        url: event.relatedTarget.href,
        context: document.body,
        error: function (response) {
            alert(response.responseText);
        }

    }).done(function (response) {
        modal.html(response);
    });
});
