$(document).ready(function () {
    var puc = $('#products').data('puc');

    $("#product-tab-header").on("click", function(){
        $("div[id$='table-div']").hide();
        $("#product-table-div").show();
        var producttable = $('#products').DataTable({
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
                }
            ],
            destroy: true,
            processing: true,
            serverSide: true,
            ordering: true,
            stateSave: true,
            ajax: "/p_json/?puc=" + puc,
        });
    });

    $("#document-tab-header").on("click", function(){
        $("div[id$='table-div']").hide();
        $("#document-table-div").show();
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
                    className: "text-center"
                }
            ],
            destroy: true,
            processing: true,
            serverSide: true,
            ordering: true,
            stateSave: true,
            ajax: "/d_json/?puc=" + puc,
        });
    });

    $("#chemical-tab-header").on("click", function(){
        $("div[id$='table-div']").hide();
        $("#chemical-table-div").show();
        var chemicaltable = $('#chemicals').DataTable({
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
                    width:"25%"
                },
                {
                    data: 2,
                    orderable: true,
                    searchable: true
                },
            ],
            destroy: true,
            processing: true,
            serverSide: true,
            ordering: true,
            stateSave: true,
            ajax: "/c_json/?puc=" + puc,
        });
    });
    $("#product-tab-header").click()
});
