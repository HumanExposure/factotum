nestedBubbleChart(500, 500, false, "dl_pucs_json/");
collapsibleTree("dl_pucs_json/tree/");

// Venn Diagram of SIDs per Group Type combination

// Get the json from views.sids_by_grouptype_ajax
$.ajax({
    type: "GET",
    contentType: "application/json; charset=utf-8",
    url: 'sid_gt_json',
    dataType: 'json',
    async: true,
    data: "{}",
    success: function (data) {
        var set_data = data["data"];
        div_id = "#venn";
        renderVenn(div_id, set_data);
    },
    error: function (result) {}
})


function renderVenn(div_id, set_data) {

    var div = d3v5.select(div_id)
    var diag = venn.VennDiagram()
    var colours = d3v5.schemeCategory10;

    div.datum(set_data).call(diag);

    var areas = d3v5.selectAll(div_id + " g")
    areas.select("path")
        .filter(function (d) {
            return d.sets.length == 1;
        })
        .style("fill-opacity", .1)
        .style("stroke-width", 5)
        .style("stroke-opacity", .8)
        .style("fill", function (d, i) {
            return colours[i];
        })
        .style("stroke", function (d, i) {
            return colours[i];
        });

    // add a tooltip
    var tooltip = d3v5.select("body").append("div")
        .attr("class", "venntooltip");

    // add listeners to all the groups to display tooltip on mouseover
    div.selectAll("g")
        .on("mouseover", function (d, i) {
            // sort all the areas relative to the current item
            venn.sortAreas(div, d);

            // Display a tooltip with the current size
            tooltip.transition().duration(400).style("opacity", .9);
            var ttlabel = d.size + " chemical(s) in \n" + d.sets.join(" + ")
            tooltip.text(ttlabel);

            // highlight the current path
            var selection = d3v5.select(this).transition("tooltip").duration(400);
            selection.select("path")
                .style("fill-opacity", d.sets.length == 1 ? .4 : .1)
                .style("stroke-width", "3")
                //.style("stroke", "white")
                .style("stroke-opacity", 1);
        })

        .on("mousemove", function () {
            tooltip.style("left", (d3v5.event.pageX) + "px")
                .style("top", (d3v5.event.pageY - 28) + "px");
        })

        .on("mouseout", function (d, i) {
            tooltip.transition().duration(400).style("opacity", 0);
            var selection = d3v5.select(this).transition("tooltip").duration(400);
            selection.select("path")
                .filter(function (d) {
                    return d.sets.length == 1;
                })
                .style("fill-opacity", .1)
                .style("stroke-width", 5)
                .style("stroke-opacity", .8)
        });

    // Is it possible or advisable to add a label to every intersection or circle?
    // var paths = div.selectAll(".venn-area")
    //     .append("text") // not sure how to assign the coordinates for these labels
    //     .attr("class", "countlabel")
    //     .attr("text-anchor", "middle")
    //     .attr("x", 300)
    //     .attr("y", 200)
    //     .text(function (d) {
    //         return d.size
    //     });
}


function grouptype_transform(rows)
{
    for (row of rows) {
        if (['Habits and practices', 'Unidentified', 'Supplemental documents'].includes(row[0]))
        {
            row[2] = '';
            row[3] = '';
        }
    }
    return rows
}

$('#grouptype_table').DataTable({
    "serverSide":   false,
    "info":         false,
    "paging":       false,
    "searching":    false,
    "ordering":     false,
    "ajax":         {
                        "url":          "grouptype/stats/",
                        "dataSrc":      function ( json ) {
                            return this.grouptype_transform(json.data);
                        },
                    },
    "columns":      [{"title": "Group Type"},
                     {"title": "Documents (%)"},
                     {"title": "Raw Chemical Records (%)"},
                     {"title": "Curated Chemical Records (%)"},]
})
