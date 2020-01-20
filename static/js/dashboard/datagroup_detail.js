// Load hover buttons
var ICON_MAP = new Map([
    [".csv", "fa-file-csv"],
    [".pdf", "fa-file-pdf"],
    [".txt", "fa-file-alt"],
    [".doc", "fa-file-word"],
    [".docx", "fa-file-word"],
    [".xls", "fa-file-excel"],
    [".xlsx", "fa-file-excel"],
    [".jpg", "fa-file-image"],
    [".tiff", "fa-file-image"],
]);
function renderDataTable(boolComp, boolHab, boolSD, fsid) {
    function renderTitle(data, type, row, meta) {
        var icon = ICON_MAP.has(row.fileext.toLowerCase()) ? ICON_MAP.get(row.fileext.toLowerCase()) : "fa-file";
        if (row.matched) {
            return [
                "<a ",
                "href='/media/" + fsid + "/pdf/document_" + row.id + row.fileext + "' ",
                "title='Link to document_" + row.id + row.fileext + "' ",
                "target='_blank'",
                ">",
                "<span class='fa " + icon + " mr-2'></span>",
                "</a>",
                "<a ",
                "href='/datadocument/" + row.id + "/' ",
                "title='Link to document detail'",
                ">",
                row.title,
                "</a>"
            ].join("");
        } else {
            return row.title;
        }
    }
    function renderTitleSD(data, type, row, meta) {
        var icon = ICON_MAP.has(row.fileext.toLowerCase()) ? ICON_MAP.get(row.fileext.toLowerCase()) : "fa-file";
        if (row.matched) {
            return [
                "<a ",
                "href='/media/" + fsid + "/pdf/document_" + row.id + row.fileext + "' ",
                "title='Link to document_" + row.id + row.fileext + "' ",
                "target='_blank'",
                ">",
                "<span class='fa " + icon + " mr-2'></span>",
                "</a>",
                row.title,
            ].join("");
        } else {
            return row.title;
        }
    }
    function renderMatched(data, type, row, meta) {
        if (row.matched) {
            return "<div class='text-secondary text-center'><span class='fa fa-check'></span><span style='display:none'>1</span></div>";
        } else {
            return [
                "<div class='text-center'>",
                "<a class='btn btn-sm btn-outline-secondary hover-danger' title='Delete' ",
                "href ='/datadocument/delete/" + row.id + "/'",
                ">",
                "<span class='fa fa-trash'></span>",
                "</a>",
                "</div>"
            ].join("");
        }
    }
    function renderExtracted(data, type, row, meta) {
        if (row.extracted) {
            return "<div class='text-secondary text-center'><span class='fa fa-check'></span><span style='display:none'>1</span></div>";
        } else {
            return "<div class='text-secondary text-center'><span class='fa fa-times'></span></div>";
        }
    }

    function renderHidden(data, type, row, meta) {
        if (row.hidden === 'Extracted') {
            return "<div>Extracted</div>";
        } else {
            return "<div>Not Extracted</div>";
        }
    }

    function renderHab(data, type, row, meta) {
        return [
            "<div class='text-center'>",
            "<a class='btn btn-sm btn-outline-secondary hover-success' title='Edit/inspect habits and practices' ",
            "href ='habitsandpractices/" + row.id + "/'",
            ">",
            "<span class='fa fa-edit'></span>",
            "</a>",
            "</div>"
        ].join("");
    }
    function renderProd(data, type, row, meta) {
        if (row.product_id) {
            return "<div class='text-center'><a href='/product/" + row.product_id + "/'>" + row.product_title + "</a></div>";
        } else {
            return "<div class='text-secondary text-center'><span class='fa fa-times'></span></div>";
        }
    }
    if (boolComp) {
        var columns = [
            { "data": "title", "render": renderTitle },
            { "data": "matched", "render": renderMatched },
            { "data": "extracted", "render": renderExtracted , "width": "13%" },
            { "data": "product", "render": renderProd },
            { "data": "hidden", "render": renderHidden },
        ];
    } else if (boolHab) {
        var columns = [
            { "data": "title", "render": renderTitle },
            { "data": "matched", "render": renderMatched },
            { "data": "edit", "render": renderHab },
        ];
    } else if (boolSD) {
        var columns = [
            { "data": "title", "render": renderTitleSD },
            { "data": "matched", "render": renderMatched },
        ];
    } else {
        var columns = [
            { "data": "title", "render": renderTitle },
            { "data": "matched", "render": renderMatched },
            { "data": "extracted", "render": renderExtracted },
        ];
    }
    if (boolComp) {
        $('#docs').DataTable({
            "ajax": "./documents_table/",
            "columns": columns,
            columnDefs: [
                    { targets: [4], visible: false },
                ],
            initComplete: function () {
                
                var extracted = this.api().columns( 2 ).every( function () {
                    return this;
                } );
    
                this.api().columns( 4 ).every( function () {
                    var column = this;
                    var select = $('<select class="custom-select"><option value="">All</option></select>')
                        .appendTo( $(extracted.footer()).empty() )
                        .on( 'change', function () {
                            var val = $.fn.dataTable.util.escapeRegex(
                                $(this).val()
                                );
                            column
                                .search( val ? '^'+val+'$' : '', true, false )
                                .draw();
                        } );
                    column.data().unique().sort().each( function ( d, j ) {
                        select.append( 
                            '<option value="'+d+'" name="'+d.replace(/ /g, '_')+'">'+d+'</option>' 
                        )
                    } );
                } );
            }
        });
    } else {
        $('#docs').DataTable({
            "ajax": "./documents_table/",
            "columns": columns,
        });
    }
}


function renderDonut(id, part, total) {
    // http://bl.ocks.org/mbostock/5100636
    var tau = 2 * Math.PI;
    var arc = d3v5.arc()
        .innerRadius(15)
        .outerRadius(20)
        .startAngle(0);
    var svg = d3v5.select("#" + id),
        width = +svg.attr("width"),
        height = +svg.attr("height"),
        g = svg.append("g").attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");
    var background = g.append("path")
        .datum({ endAngle: tau })
        .style("fill", "#CCCCCC")
        .attr("d", arc);
    var foreground = g.append("path")
        .datum({ endAngle: 0.0 * tau })
        .style("fill", "#3B3B3B")
        .attr("d", arc);
    d3v5.timeout(function () {
        foreground.transition()
            .duration(1000)
            .attrTween("d", arcTween((part / total) * tau));
    }, 500);
    function arcTween(newAngle) {
        return function (d) {
            var interpolate = d3v5.interpolate(d.endAngle, newAngle);
            return function (t) {
                d.endAngle = interpolate(t);
                return arc(d);
            };
        };
    }
}

async function setTaskState(tab_switched) {
    async function getJSON(url) {
        var json = await fetch(url).then(res => res.json());
        return json;
    }

    async function getTaskToForm() {
        // Returns an array of task_id to form name
        var all_user_tasks = await getJSON("/api/tasks/");
        var datagroup_pk = window.location.pathname.split("/")[2];
        return _.chain(all_user_tasks)
            .filter(o => o.name.split(".")[1] == datagroup_pk)
            .groupBy("task")
            .mapValues(o => o[0].name.split(".")[0])
            .value();
    }

    async function getTasks() {
        // Returns an array of each form's status
        var task_to_form = await getTaskToForm();
        var task_ids = _.chain(task_to_form)
            .keys(task_to_form)
            .join(",")
            .value();
        if (!_.isEmpty(task_ids)) {
            var all_task_status = await getJSON(`/api/tasks/${task_ids}/`);
            return _.chain(all_task_status)
                .values()
                .map(o => {
                    o.form = task_to_form[o.task_id];
                    return o;
                })
                .uniqBy("form")
                .value();
        } else {
            return [];
        }
    }

    function shouldSpin(task) {
        // Returns whether the spinner spin
        return ["PENDING", "RECEIVED", "STARTED", "PROGRESS", "RETRY"].includes(
            task.status
        );
    }

    function showErrorButton(task) {
        // Returns whether the "View Errors" button should be shown
        return ["FAILURE", "RETRY"].includes(task.status);
    }

    function getSpinnerColor(task) {
        // Returns the spinner color
        if ("PENDING" == task.status) {
            return "secondary";
        } else if (["RECEIVED", "STARTED", "PROGRESS"].includes(task.status)) {
            return "primary";
        } else if ("SUCCESS" == task.status) {
            return "success";
        } else if ("FAILURE" == task.status) {
            return "danger";
        } else if (["RETRY", "REVOKED"].includes(task.status)) {
            return "warning";
        }
    }

    function getMessage(task) {
        // Returns the message to be displayed below the spinner
        switch (task.status) {
            case "PENDING":
                var msg = "The upload has been submitted...";
                break;
            case "RECEIVED":
                var msg = "Processing has begun...";
                break;
            case "STARTED":
                var msg = "Processing has begun...";
                break;
            case "PROGRESS":
                var msg = task.result.description;
                break;
            case "SUCCESS":
                var msg = `This upload has completed successfully.<br>${task.result.toLocaleString()} records have been uploaded.`;
                break;
            case "FAILURE":
                var msg = "This upload has failed.";
                break;
            case "REVOKED":
                var msg = "This upload has been cancelled.";
                break;
            case "RETRY":
                var msg = "This upload has failed, but is being resubmitted...";
                break;
        }
        return msg;
    }

    function getFormErrors(task) {
        // Returns the ul element representation of errors
        var root = document.createElement("ul");
        // "Non-form" errors
        _.forEach(task.result.non_form_errors, o => {
            var li = document.createElement("li");
            li.innerHTML = o.message;
            root.appendChild(li);
        });
        // "Form" errors
        var num = 1;
        _.forEach(task.result.form_errors, form_errors => {
            num++;
            if (!_.isEmpty(form_errors)) {
                var row_li = document.createElement("li");
                row_li.innerHTML = `Row ${num}`;
                var field_ul = document.createElement("ul");
                _.mapKeys(form_errors, (field_errors, field) => {
                    var field_li = document.createElement("li");
                    field_name = field == "__all__" ? "All fields" : field;
                    field_li.innerHTML = `Field <code>${field}</code>`;
                    var error_ul = document.createElement("ul");
                    _.forEach(field_errors, error => {
                        var error_li = document.createElement("li");
                        error_li.innerHTML = error.message;
                        error_ul.appendChild(error_li);
                    });
                    field_li.appendChild(error_ul);
                    field_ul.appendChild(field_li);
                });
                row_li.appendChild(field_ul);
                root.appendChild(row_li);
            }
        });
        return root;
    }

    function setElements(task) {
        // Sets all the elements on the webpage for a task
        // Gather elements
        var form_el = document.getElementById(`${task.form}-form`);
        var task_el = document.getElementById(`${task.form}-task`);
        var msg_el = task_el.getElementsByClassName("formtask-status")[0];
        var spinner_el = task_el.getElementsByClassName("formtask-spinner")[0];
        var time_el = task_el.getElementsByClassName("formtask-time")[0];
        var err_btn_el = task_el.getElementsByClassName("formtask-err-btn")[0];
        var err_exctype_el = task_el.getElementsByClassName(
            "formtask-error-exctype"
        )[0];
        var err_excmsg_el = task_el.getElementsByClassName(
            "formtask-error-excmsg"
        )[0];
        var err_modal_el = task_el.getElementsByClassName(
            "formtask-error-modal"
        )[0];
        var err_trcdiv_el = task_el.getElementsByClassName(
            "formtask-error-traceback"
        )[0];
        var err_trcmsg_el = task_el.getElementsByClassName(
            "formtask-error-tracebackmsg"
        )[0];
        var err_form_el = task_el.getElementsByClassName(
            "formtask-error-form"
        )[0];
        var del_btn_el = task_el.getElementsByClassName("formtask-del-btn")[0];

        // Message
        msg_el.innerHTML = getMessage(task);

        // Spinner
        var spinner_color = getSpinnerColor(task);
        spinner_el.className = spinner_el.className.replace(/text-\w+/g, "");
        spinner_el.className = spinner_el.className.replace(/border-\w+/g, "");
        spinner_el.className += shouldSpin(task)
            ? `text-${spinner_color}`
            : `border-${spinner_color}`;

        // Time
        var time_str = task.date_done ? task.date_done : task.result.time;
        var time = new Date(time_str + "Z");
        time_el.innerHTML = time.toLocaleString();

        // Error
        // button
        var err_modal_id = `${task.form}-modal`;
        err_modal_el.setAttribute("id", err_modal_id);
        err_btn_el.setAttribute("data-target", `#${err_modal_id}`);
        err_btn_el.style.display = showErrorButton(task) ? "" : "none";
        // exception messages
        err_exctype_el.innerHTML = task.result.exc_type;
        err_excmsg_el.innerHTML = task.result.exc_message;
        // traceback
        err_trcdiv_el.style.display = task.traceback ? "" : "none";
        if (task.traceback) {
            var traceback = task.traceback;
            traceback = traceback.replace("<", "&lt;");
            traceback = traceback.replace(">", "&gt;");
            traceback = traceback.trim();
            err_trcmsg_el.innerHTML = traceback;
        }
        // form
        err_form_el.innerHTML = "";
        err_form_el.appendChild(getFormErrors(task));

        // Dismiss
        del_btn_el.onclick = () => dismissTask(task.task_id, task.form);
        del_btn_el.disabled = false;
        del_btn_el.classList.remove("disabled");
        del_btn_el.style.display = shouldSpin(task) ? "none" : "";

        // Show the task info
        form_el.style.display = "none";
        task_el.style.display = "";
    }

    var forms = [
        "cleancomp_formset",
        "productupload_form",
        "extfile_formset",
        "uploaddocs_form"
    ];
    // Set task status
    var tasks = await getTasks();
    _.forEach(tasks, task => {
        setElements(task);
        if (!tab_switched) {
            $(`#upload-tabs a[href="#${task.form}"]`).tab("show");
            tab_switched = true;
        }
    });
    // Set non-task forms
    var nontask_forms = _.difference(forms, _.map(tasks, "form"));
    _.forEach(nontask_forms, form => {
        var form_el = document.getElementById(`${form}-form`);
        var task_el = document.getElementById(`${form}-task`);
        if (form_el && task_el) {
            form_el.style.display = "";
            task_el.style.display = "none";
        }
    });
}

function dismissTask(task_id, form) {
    var task_el = document.getElementById(`${form}-task`);
    var del_btn_el = task_el.getElementsByClassName("formtask-del-btn")[0];
    del_btn_el.classList.add("disabled");
    del_btn_el.disabled = true;
    fetch(`/api/tasks/${task_id}`, {
        method: "DELETE",
        headers: { "X-CSRFToken": Cookies.get("csrftoken") }
    }).then(setTaskState(true));
}

$(document).ready(function() {
    setTaskState(false);
    setInterval(() => setTaskState(true), 5000);
    var tableData = JSON.parse(
        document.getElementById("tabledata").textContent
    );
    renderDataTable(
        tableData.boolComp,
        tableData.boolHab,
        tableData.boolSD,
        tableData.fsid
    );
    renderDonut("matcheddonut", tableData.nummatched, tableData.numregistered);
    if (!tableData.boolSD) {
        renderDonut(
            "extracteddonut",
            tableData.numextracted,
            tableData.numregistered
        );
    }
});
