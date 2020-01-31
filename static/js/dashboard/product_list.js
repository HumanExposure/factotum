$(document).ready(function () {
    var oTable = $('#products').dataTable({
        order: [[ 0, "desc" ]],
        columns: [
            {
                data: 'title',
                orderable: true,
                searchable: true
            },
            {
                data: 'brand_name',
                orderable: true,
                searchable: true,
            }
        ],
        processing: true,
        serverSide: true,
        stateSave: true,
        ajax: "/p_json/",
    });
});