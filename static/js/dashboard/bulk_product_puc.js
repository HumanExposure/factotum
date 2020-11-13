$(document).ready(function () {
    let table_settings = JSON.parse(document.getElementById('table_settings').textContent);
    let product_table = $('#products').DataTable({
        "bPaginate": table_settings.pagination,
        "pageLength": table_settings.pageLength,
        "bFilter": false,
        columnDefs: [
            {
                orderable: false,
                className: 'select-checkbox',
                targets: 0,
                width: '3%'
            },
            {width: '40%', targets: 1},
            {width: '27%', targets: 2},
            {className: 'hide_column', targets: 3},
            {
                width: '30%',
                targets: 4
            },
        ],
        select: {
            style: 'multi',
            selector: 'td:first-child'
        },
        order: [
            [1, 'asc']
        ],
        "initComplete": function (settings, json) {
            $("div#products_info").insertAfter('div#products_wrapper');
        }
    });
    product_table.on("click", "th.select-checkbox", function () {
        if ($("th.select-checkbox").hasClass("selected")) {
            product_table.rows().deselect();
            $(product_table).removeClass("selected");
        } else {
            product_table.rows().select();
            $("th.select-checkbox").addClass("selected");
        }
    }).on("select deselect", function () {
        if (product_table.rows({
            selected: true
        }).count() !== product_table.rows().count()) {
            $("th.select-checkbox").removeClass("selected");
        } else {
            $("th.select-checkbox").addClass("selected");
        }
    });
    $('#btn-assign-puc').click(function (e) {
        pk_data = product_table.rows({selected: true});
        pk = '';
        for (i = 0; i < pk_data.count(); i++) {
            pk += pk_data.data()[i][3] + ',';
        }
        pk = pk.replace(/,$/g, '');
        $('input[name="id_pks"]').val(pk);
        return true;
    });
});
