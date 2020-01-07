$(document).ready(function(){
  document.querySelectorAll(".puc-link").forEach(puc => {
    var gen_cat = puc.getAttribute('data-gen-cat');
    puc.style.backgroundColor = pucColors.get(gen_cat)
  })
});