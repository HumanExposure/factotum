$(document).ready(function () {
  var table = $('#products').DataTable({
      "serverSide": true,
      "paging": true,
      "searching": true,
      "ordering": true,
      "ajax": "/p_json/",
      dom: "<'row'<'col-md-4 form-inline'l><'col-md-4 form-inline'f>>" +
          "<'row'<'col-sm-12'tr>>" +
          "<'row'<'col-sm-5'i><'col-sm-7'p>>", // order the control divs
      "columns": [
          {
              name: "title",
              "width": "50%",
              "render": function ( data, type, row ) {
                  return '<a href="/product/' + row[2] + '"' + ' title="Link to product detail">' + data + '</a>';
              }
          },
          {
              name: "brand_name",
              "width": "20%"
          },
          {
              "width": "30%",
              "orderable": false,
              "render": function ( data, type, row ) {
                  return '---';
              }
          }
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