import ajax_form_request from '../modules/ajax_form_submission.js'


// Submit post on submit
$('#extracted-text-form').on('submit', function(event){
    event.preventDefault();
    ajax_form_request('#extracted-text-form').done(function(){
        location.reload()
    })
});
