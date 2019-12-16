$('#id_tags').addClass('taggit-labels taggit-list')

$(document).ready(function($) {
    var inputs = $(this).find(".taggit-labels + input")[0]
    var tagList = inputs.value.split(", ")
    tagList.indexOf("") === -1 ? tagList.push("") : tagList
    $("#tag_submit").attr('disabled', 'disabled');
    $(".taggit-tag").click(function(){
        var tag = $(this).text()
        var curList = $('.taggit-labels + input')[0].value.split(", ")
        curList.indexOf("") === -1 ? curList.push("") : curList
        if (curList.includes(tag)){
            curList = curList.filter(function(e) { return e !== tag })
        }else {
            curList.push($(this).text())
        }
        if (curList.sort().join(',') === tagList.sort().join(',')){
            $("#tag_submit").attr('disabled', 'disabled');
        }else{
            $("#tag_submit").removeAttr("disabled");
        }
    })
});
