nestedBubbleChart(500, 500, "dl_pucs_json/");
collapsibleTree("dl_pucs_json/tree/");

$('#grouptype_table').DataTable({
    "serverSide":   false,
    "info":         false,
    "paging":       false,
    "searching":    false,
    "ordering":     false,
    "ajax":         "grouptype/stats/",
});
