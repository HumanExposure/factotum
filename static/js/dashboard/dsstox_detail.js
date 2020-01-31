$(document).ready(function () {
    var url = '/d_json/?chem_detail=True&sid=' + $('#documents').data('sid');
    var documenttable = $('#documents').DataTable({
        columns: [
            {
                data: 0,
                orderable: true,
                searchable: true
            },
            {
                data: 1,
                orderable: true,
                searchable: true,
                className: "text-center",
                width: "30%"
            }
        ],
        dom: "<'row'<'col-6 form-inline'l><'col-6 form-inline'f>>" +
            "<'row'<'col-12 p-0'tr>>" +
            "<'row'i>" +
            "<'row'<'ml-auto'p>>",
        destroy: true,
        processing: true,
        serverSide: true,
        ordering: true,
        // stateSave: true,
        drawCallback: () => {
            $('.paginate_button').on('click', moveText);
        },
        ajax: url,
        initComplete: function () {
            $('#info_text').text($('#documents_info').text())
        }
    });

    $('a[id^="filter-"]').on('click', e => {
        var puc = $(e.currentTarget).data('pk');
        documenttable.ajax.url(url + '&category=' + puc).load(moveText);
        $('#reset').prop('disabled', false);
    });
    $('a[id^="keywords-"]').on('click', e => {
        var pid = $(e.currentTarget).data('presence-id');
        documenttable.ajax.url(url + '&pid=' + pid).load(moveText);
        $('#reset').prop('disabled', false);
    });

    $('#group_type_dropdown').on('change', e => {
        var group_type = $(e.currentTarget).children("option:selected").val()
        documenttable.ajax.url(url + '&group_type=' + group_type).load(moveText);
        $('#reset').prop('disabled', false);
    });

    $('#reset').on('click', function (e) {
        documenttable.ajax.url(url).load(moveText);
        console.log($(this).prop('disabled', true));
    });

    var moveText = () => {
        $('#info_text').text($('#documents_info').text());
    }
    
    documenttable.on('draw', moveText)
});

$('.handle').on('click', function (e) {
    $(this).find('svg').toggleClass('d-none');
});

$('#flipbtn').on('click', function (e) {
    if (this.innerHTML == "Show Table"){
        this.innerHTML = "Show PUCs";
    } else {
        this.innerHTML = "Show Table";
    }
    $("#nestedcircles").toggleClass('trans-bubble');
    $("#tbldiv").toggleClass('trans-table');
});
