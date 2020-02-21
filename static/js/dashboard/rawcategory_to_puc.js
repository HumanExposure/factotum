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
  }
};

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
