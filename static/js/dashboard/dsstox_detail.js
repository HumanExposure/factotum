var truncate_chars = (words) => {
    if (words.length >= 47) {
        return words.slice(0, 44) + '...'
    } else {
        return words
    }
};

var table = $('#keywords').DataTable({
    "ajax": "",
    "language": {
        "emptyTable": "Click on Keyword sets for list of DataDocuments."
    },
    dom: "<'row'<'col-6 form-inline'l><'col-6 form-inline'f>>" +
        "<'row'<'col-12'tr>>" +
        "<'row'<'col-6 ml-auto'p>>" +
        "<'row'<'col-6 ml-auto'i>>",
    "columns": [{
        data: "title",
        "render": function (data, type, row) {
            return ('<a href="/datadocument/' + row.id + '"' +
                ' title="Link to document detail" target="_blank">' +
                truncate_chars(data) + '</a>');
        }
    }, ],
});

$(document).ready(function () {
    document.querySelectorAll(".puc-link").forEach(puc => {
        var gen_cat = puc.getAttribute('data-gen-cat');
        puc.style.backgroundColor = pucColors.get(gen_cat)
    })

    var sid = $('#documents').data('sid')
    var documenttable = $('#documents').DataTable({
        "serverSide": true,
        "paging": true,
        "searching": true,
        "ordering": true,
        "ajax": "/d_json/?sid=" + sid,
        dom: "<'row'<'col-6 form-inline'l><'col-6 form-inline'f>>" +
            "<'row'<'col-12'tr>>" +
            "<'row'<'col-6'i><'col-6'p>>", // order the control divs
        "columns": [{
                name: "document",
                // "width": "70%",
                "render": function (data, type, row) {
                    return '<a href="/datadocument/' + row[2] + '"' + ' title="Link to document">' + data + '</a>';
                }
            },
            {
                name: "data_group__group_type__title",
                // "width": "30%"
            },
        ],
        "initComplete": function (settings, json) {
            $('#documents_filter input').unbind();
            $('#documents_filter input').bind('keyup', function (e) {
                if (e.keyCode == 13) {
                    documenttable.search(this.value).draw();
                }
            });
        }
    });
});

$('.handle').on('click', function (e) {
    $(this).find('svg').toggleClass('d-none');
});



$('div[id^="keywords-"]').on('click', e => {
    var pid = $(e.currentTarget).data('presence-id');
    table.ajax.url('/keywordset_documents/' + pid + '/').load();
});