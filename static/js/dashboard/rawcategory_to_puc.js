// Bootstrap 4 fix for ProductPUCForm drop-down.
//
// https://github.com/sweetalert2/sweetalert2/issues/374#issuecomment-494174745
$.fn.modal.Constructor.prototype._enforceFocus = function() {};

var rows = JSON.parse(document.getElementById('tabledata').textContent);

var columnDefs = [
  {headerName: "Data Group", field: "data_group__name", cellRenderer: 'groupCellRenderer'},
  {headerName: "Raw Category", field: "raw_category"},
  {headerName: "Count", field: "document_count"},
];

var rowData = rows;

// let the grid know which columns and what data to use
var gridOptions = {
  defaultColDef: {
    sortable: true,
    resizable: true,
    filter: true
  },
  columnDefs: columnDefs,
  rowData: rowData,
  components: {
    'groupCellRenderer': GroupCellRenderer
  },
  domLayout: 'autoHeight',
  pagination: true,
  onGridReady: function (params) {
    // Enable column resize on load
    params.api.sizeColumnsToFit();

    // Enable column resize on page size change
    window.addEventListener('resize', function() {
      setTimeout(function() {
        params.api.sizeColumnsToFit();
      })
    })
  },
  rowSelection: 'multiple',
  onSelectionChanged: onSelectionChanged,
};

function onSelectionChanged() {
    var selectedRows = gridOptions.api.getSelectedRows();
    var selectedRowsString = '';
    var selectedRowsList = '';
    var selectedRowsArray = [];
    var maxToShow = 5;

    selectedRows.forEach(function(selectedRow, index) {
        if (index >= maxToShow) {
            return;
        }

        if (index > 0) {
            selectedRowsString += ', ';
        }

        selectedRowsString += selectedRow.data_group__name;
        selectedRowsList += "<li>" + selectedRow.data_group__name + " - " + selectedRow.raw_category + "</li>"
        selectedRowsArray.push({"datagroup": selectedRow.data_group__id, "raw_category": selectedRow.raw_category})
    });

    if (selectedRows.length > maxToShow) {
        var othersCount = selectedRows.length - maxToShow;
        selectedRowsString += ' and ' + othersCount + ' other' + (othersCount !== 1 ? 's' : '');
    }

    document.querySelector('#selectedRows').innerHTML = selectedRowsString;
    document.querySelector('#selectedRowsList').innerHTML = selectedRowsList;
    document.querySelector('#datagroup_rawcategory_groups').value = JSON.stringify(selectedRowsArray)

    if (selectedRows) {
        document.getElementById('pucModalBtn').disabled = false
    }
    else {
        document.getElementById('pucModalBtn').disabled = true
    }
}

// cell renderer class
function GroupCellRenderer() {}

// init method gets the details of the cell to be rendered
GroupCellRenderer.prototype.init = function(params) {
    this.eGui = document.createElement('div');
    this.eGui.classList.add('d-flex', 'justify-content-between');
    var text = (
        '<span class="text-truncate">' +
            params.data.data_group__name +
        '</span>'+
        '<a class="text-secondary" href="/datagroup/' + params.data.data_group__id + '">' +
            '<i class="fas fa-info-circle"></i>' +
        '</a>'
    );
    this.eGui.innerHTML = text;
};

GroupCellRenderer.prototype.getGui = function() {
    return this.eGui;
};

// setup the grid after the page has finished loading
document.addEventListener('DOMContentLoaded', function() {
    var gridDiv = document.querySelector('#bulkPucGrid');
    new agGrid.Grid(gridDiv, gridOptions);
});
