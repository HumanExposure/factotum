$('#funcuse-add').click(function (e) {
    $('div.mystical').filter(':first').removeClass("mystical");
    if ($('div.mystical').filter(':first').length == 0){
        $('#funcuse-add').hide();
    }
})