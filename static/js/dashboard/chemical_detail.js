var documents_url, products_url;

$(document).ready(function () {
    documents_url = '/d_json/?chem_detail=True&sid=' + $('#documents').data('sid');
    products_url = '/chemical_product_json?sid=' + $('#products').data('sid');

    var documenttable = build_document_table();
    var producttable = build_product_table();

    $('a[id^="filter-"]').on('click', e => {
        var puc = $(e.currentTarget).data('pk');
        documenttable.ajax.url(documents_url + '&category=' + puc).load(moveText);
        producttable.ajax.url(products_url + '&category=' + puc).load(moveText);
        $('#reset-documents').prop('disabled', false);
        $('#reset-products').prop('disabled', false);
    });
    $('a[id^="keywords-"]').on('click', e => {
        var pid = $(e.currentTarget).data('presence-id');
        documenttable.ajax.url(documents_url + '&pid=' + pid).load(moveText);
        $('#reset-documents').prop('disabled', false);
    });
    $('#group_type_dropdown').on('change', e => {
        var group_type = $(e.currentTarget).children("option:selected").val();
        documenttable.ajax.url(documents_url + '&group_type=' + group_type).load(moveText);
        $('#reset-documents').prop('disabled', false);
    });
    $('#reset-documents').on('click', function (e) {
        documenttable.ajax.url(documents_url).load(moveText);
        $(this).prop('disabled', true);
    });
    $('#reset-products').on('click', function (e) {
        producttable.ajax.url(products_url).load(moveText);
        $(this).prop('disabled', true);
    });
    var moveText = () => {
        $('#documents_info_text').text($('#documents_info').text());
        $('#products_info_text').text($('#products_info').text());
    };

    documenttable.on('draw', moveText);
    producttable.on('draw', moveText);
});

function build_document_table() {
    return $('#documents').DataTable({
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
            // $('.paginate_button').on('click', moveText);
        },
        ajax: documents_url,
        initComplete: function () {
            $('#documents_info_text').text($('#documents_info').text())
        }
    });
}

function build_product_table() {
    return $('#products').DataTable({
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
            },
            {
                data: 2,
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
            // $('.paginate_button').on('click', moveText);
        },
        ajax: products_url,
        initComplete: function () {
            $('#products_info_text').text($('#products_info').text())
        }
    });
}
