$(document).ready(function () {
  var puc = $('#products').data('puc')
  var table = $('#products').DataTable({
      "serverSide": true,
      "paging": true,
      "searching": true,
      "ordering": true,
      "ajax": "/p_json/?puc=" + puc,
      dom: "<'row'<'col-6 form-inline'l><'col-6 form-inline'f>>" +
          "<'row'<'col-12'tr>>" +
          "<'row'<'col-6'i><'col-6'p>>", // order the control divs
      "columns": [
          {
              name: "title",
              // "width": "70%",
              "render": function ( data, type, row ) {
                  return '<a href="/product/' + row[2] + '"' + ' title="Link to product detail">' + data + '</a>';
              }
          },
          {
              name: "brand_name",
              // "width": "30%"
          },
      ],
      "initComplete": function(settings, json) {
          $('#products_filter input').unbind();
          $('#products_filter input').bind('keyup', function(e) {
              if(e.keyCode == 13) {
                  table.search( this.value ).draw();
              }
          });
      }
  });
});
