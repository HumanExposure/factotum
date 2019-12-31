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