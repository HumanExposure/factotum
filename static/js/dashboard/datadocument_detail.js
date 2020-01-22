$(document).ready(function () {

    var title_height = $('#title').height();
    var scroll_height = $(window).height() - (title_height + 80);
    $('.scroll-div').css('max-height', scroll_height);

    //create static slider for each chemical card
    document.querySelectorAll(".wf-analysis").forEach(wf_analysis => {
        var chemical_pk = wf_analysis.getAttribute('data-chemical-pk');
        var lower = wf_analysis.getAttribute('data-lower-wf-analysis');
        var central = wf_analysis.getAttribute('data-central-wf-analysis');
        var upper = wf_analysis.getAttribute('data-upper-wf-analysis');
        var input_id = 'wf_slider_' + chemical_pk;
        if (central) {
            range = false;
            value = [parseFloat(central), parseFloat(central)];
        } else {
            range = true;
            value = [parseFloat(lower.length === 0 ? '0' : lower),
                     parseFloat(upper.length === 0 ? '0' : upper)];
        }
        $('#' + input_id)
            .slider({
                id: "slider" + chemical_pk,
                min: 0,
                max: 1,
                step: .00001,
                ticks: [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1],
                ticks_labels: ['0', '', '', '', '', '', '', '', '', '', '1'],
                range: range,
                value: value,
                enabled: false,
                precision: 15,
                formatter: function (value) {
                    return 'Weight fraction analysis: ' + ((value[0] === value[1]) ? value[0] : value[0] + ' - ' + value[1]);
                }
            });
    })
});

$('[id^=chem-click-]').click(function (e) {
    // add click event to bring active element into focus when many chems
    scrollNav = $("#scroll-nav");
    scrollNav.animate({
        scrollTop: $(".active p").offset().top - scrollNav.offset().top + scrollNav.scrollTop() - 47
    });
})

// update location for the reload that happens when editing chemical
$("#chem-scrollspy").ready(function () {
    var chem = location.href.split("#").length
    if (chem > 1) {
        location.href = location.href
    }
});

// add color to elements on hover...
$('.hover').mouseover(function () {
    $(this).removeClass("btn-outline-secondary");
    $(this).addClass("btn-" + this.name);
})

$('.hover').mouseout(function () {
    $(this).removeClass("btn-" + this.name);
    $(this).addClass("btn-outline-secondary");
})

$('#chemical-add-modal').on('show.bs.modal', function (event) {
    var modal = $(this);
    $.ajax({
        url: modal.attr('data-url'),
        context: document.body
    }).done(function (response) {
        modal.html(response);
    });
});

$('#chemical-update-modal').on('show.bs.modal', function (event) {
    var modal = $(this);
    var chem_pk = event.relatedTarget.value;
    $.ajax({
        url: modal.attr('data-url').replace(/47/, chem_pk.toString()),
        context: document.body
    }).done(function (response) {
        modal.html(response);
    });
});

$('#chemical-audit-log-modal').on('show.bs.modal', function (event) {
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
