function csTypo() {
    $('.ls-block').each(function(index, value){
      var str = $(this).html();
      str = str.replace(/(\s|^)(a|i|k|o|s|u|v|z)(\s+)([^\p{Cc}\p{Cf}\p{zL}\p{Zp}]+)/gmi , '$1$2&nbsp;$4');
      $(this).html(str);    
    })
  }
  
  window.addEventListener("load", syntaxHighlights);