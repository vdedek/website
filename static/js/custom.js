function csTypo() {
    $('.ls-block').each(function(index, value) {
      var str = $(this).html();
      // Updated regular expression to handle "a" and other single-letter words
      str = str.replace(/(\s|^)([aikosuvz])(\s+)([^\p{Cc}\p{Cf}\p{zL}\p{Zp}]+)/gmi, '$1$2&nbsp;$4');
      $(this).html(str);
    });
  }
  
  window.addEventListener("load", csTypo); // Corrected function name here
  