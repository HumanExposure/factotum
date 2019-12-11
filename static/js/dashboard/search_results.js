$(document).ready(function () {
  $('input:checkbox').prop('checked', false);
  checkBoxes();

function addParam(v) {
  var page = window.location.search.indexOf('page=')
  if (page > 0){
    window.location.search = window.location.search.substr(0,page) + v
  }
  else {
    window.location.search += '&' + v;
  }
}

function checkBoxes() {
  var filterForm = document.getElementById("filter-form");
  var params = new URLSearchParams(window.location.href);
  var facets = ["datadocument_grouptype", "product_brandname", "product_manufacturer", "puc_gencatfacet"]
  facets.forEach(function (facet) {
    var param_str = params.get(facet)
    var param_arr = param_str ? param_str.split(",") : [];
    param_arr.forEach(function (entry) {
      var name = atob(entry);
      [...filterForm.elements].forEach(function (entry) {
        var facetName = entry.id.split("-")[0];
        var inputValue = entry.name;
        if (facetName == facet && inputValue == name) {
          entry.checked = true;
        }
      })
    })
  })
}

$('#filterButton').on('click', function (event) {
  // Base64 encode input
  var filterForm = document.getElementById("filter-form");
  var facet = {
    "datadocument_grouptype": [],
    "product_brandname": [],
    "product_manufacturer": [],
    "puc_gencatfacet": [],
  };
  [...filterForm.elements].forEach(function (entry) {
    if (entry.checked) {
      var facetName = entry.id.split("-")[0];
      var inputValue = entry.name;
      facet[facetName].push(btoa(inputValue));
    }
  })
  var queryStr = "?q=" + window.location.search.split("q=")[1].split("&")[0];
  Object.keys(facet).forEach(function (key) {
    if (facet[key].length > 0) {
      queryStr += "&" + key + "=" + facet[key].join(",");
    }
  })
  window.location.search = queryStr;
});

$('#clearfilterButton').on('click', function (event) {
  var queryStr = "?q=" + window.location.search.split("q=")[1].split("&")[0];
  window.location.search = queryStr;
})