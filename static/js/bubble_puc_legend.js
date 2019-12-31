$(document).ready(function(){
  document.querySelectorAll(".puc-link").forEach(puc => {
    var gen_cat = puc.getAttribute('data-gen-cat');
    puc.style.backgroundColor = pucColors.get(gen_cat)
  })
});

$('.handle').on('click', function (e) {
  $(this).find('svg').toggleClass('d-none');
});

$('div[id^="keywords-"]').on('click', e =>{
  var pid = $(e.currentTarget).data('presence-id');
  table.ajax.url( '/keywordset_documents/' + pid + '/' ).load();
});
