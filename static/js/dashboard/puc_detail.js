$(document).ready(function () {
    var puc = $('#products').data('puc')

    $("#productos").on("click", function(){
        $("div[id$='table-div']").hide()
        $("#prod-table-div").show()
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
    })

    $("#documentos").on("click", function(){
        $("div[id$='table-div']").hide()
        $("#doc-table-div").show()
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
    })

    $("#quimicos").on("click", function(){
        $("div[id$='table-div']").hide()
        $("#chem-table-div").show()
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
    })
    $("#productos").click()
});
