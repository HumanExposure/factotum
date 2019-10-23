$(document).ready(function () {
  var table = $('#extraction_script_table').DataTable({
  "columnDefs": [
      {
          "targets": 3,
          "orderable": false
      }
  ],
  dom:"<'row'<'col-md-4 form-inline'l><'col-md-4 form-inline'f>>" +
      "<'row'<'col-sm-12 text-center'tr>>" +
      "<'row'<'col-sm-5'i><'col-sm-7'p>>" // order the control divs
  });
});

