var rows = JSON.parse(document.getElementById('tabledata').textContent);

var columnDefs = [
  {headerName: "Group Type", field: "group_type__title"},
  {headerName: "Name", field: "name"},
  {headerName: "Data Source", field: "data_source",
        cellRenderer: function (params) {
            return '<a target="_blank" href="/datasource/' + params.data.data_source + '">' + params.data.data_source__title + '</a>';
        }
  },
  {headerName: "Downloaded By", field: "downloaded_by__username"},
  {headerName: "Downloaded At", field: "downloaded_at",
        cellRenderer: (params) => {
            return moment(params.data.downloaded_at).format('ll');
      }
  },
  {headerName: "Extracted Documents", field: "num_extracted"},
  {headerName: "Link to Download Script", field: "download_script",
        cellRenderer: function (params) {
            if(params.data.download_script) {
                return '<a target="_blank" href="' + params.data.download_script__url + '">' + params.data.download_script__title + '</a>';
            }
        }
  },
  {headerName: "Options", cellRenderer: "detailRenderer"},
];

var rowData = rows;

// let the grid know which columns and what data to use
var gridOptions = {
  defaultColDef: {
    sortable: true,
    resizable: true,
    filter: true,
    wrapText: true,
    autoHeight: true,
    cellStyle: {'white-space': 'normal'},
  },
  columnDefs: columnDefs,
  rowData: rowData,
  components: {
    'detailRenderer': DetailRenderer,
  },
  domLayout: 'autoHeight',
  pagination: true,
  paginationPageSize: 50,
  onColumnResized: function (params) {
        params.api.resetRowHeights();
  },
  onGridReady: function (params) {
    // Enable column resize on load
    params.api.sizeColumnsToFit();

    // Enable column resize on page size changepaginationPageSize
    window.addEventListener('resize', function() {
      setTimeout(function() {
        params.api.sizeColumnsToFit();
      })
    })
  },
};

// cell renderer class
function DetailRenderer() {}

// init method gets the details of the cell to be rendered
DetailRenderer.prototype.init = function(params) {
    this.eGui = document.createElement('div');
    this.eGui.classList.add('d-flex', 'justify-content-between');
    var text = (

        '<a class="btn btn-info btn-sm" role="button" title="Details" href="/datagroup/' + params.data.id + '">' +
            '<i class="fa fa-fs fa-info-circle"></i>' +
        '</a>' +
        '<a class="btn btn-info btn-sm" role="button" title="Edit" href="/datagroup/edit/' + params.data.id + '">' +
            '<i class="fa fa-fs fa-edit"></i>' +
        '</a>' +
        '<a class="btn btn-info btn-sm" role="button" title="Delete" href="/datagroup/delete/' + params.data.id + '">' +
            '<i class="fa fa-fs fa-trash"></i>' +
        '</a>'

    );
    this.eGui.innerHTML = text;
};

DetailRenderer.prototype.getGui = function() {
    return this.eGui;
};

//Clear all filters
function clearFilters() {
  gridOptions.api.setFilterModel(null);
}

//Filter search box
function onFilterTextBoxChanged() {
    gridOptions.api.setQuickFilter(document.getElementById('filter-text-box').value);
}

//Change the amount of rows to paginate table
function onPageSizeChanged(newPageSize) {
  var value = document.getElementById('page-size').value;
  if(value == "All"){
      // this.clearFilters()
      value = gridOptions.api.paginationGetRowCount()
  }
  gridOptions.api.paginationSetPageSize(Number(value));
}

// setup the grid after the page has finished loading
document.addEventListener('DOMContentLoaded', function() {
    var gridDiv = document.querySelector('#datagroupGrid');
    new agGrid.Grid(gridDiv, gridOptions);
});

