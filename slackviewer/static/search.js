//<![CDATA[
$(window).load(function(){
function searchAndHighlight(searchTerm, selector) {
    if (searchTerm) {
        //var wholeWordOnly = new RegExp("\\g"+searchTerm+"\\g","ig"); //matches whole word only
        //var anyCharacter = new RegExp("\\g["+searchTerm+"]\\g","ig"); //matches any word with any of search chars characters
        var selector = selector || "#realTimeContents"; //use body as selector if none provided
        var searchTermRegEx = new RegExp(searchTerm, "ig");
        var matches = $(selector).text().match(searchTermRegEx);
        if (matches != null && matches.length > 0) {
            $('.highlighted').removeClass('highlighted'); //Remove old search highlights  

            //Remove the previous matches
            $span = $('#realTimeContents span.match');
            $span.replaceWith($span.html());

    if (searchTerm === "&") {
        searchTerm = "&amp;";
        searchTermRegEx = new RegExp(searchTerm, "ig");
    }
            $(selector).html($(selector).html().replace(searchTermRegEx, "<span class='match'>" + searchTerm + "</span>"));
            $('.match:first').addClass('highlighted');

            var i = 0;

            $('.next_h').off('click').on('click', function () {
                i++;

                if (i >= $('.match').length) i = 0;

                $('.match').removeClass('highlighted');
                $('.match').eq(i).addClass('highlighted');
                
				
				$(window).scrollTop($('.match').eq(i).position().top);
            });
            $('.previous_h').off('click').on('click', function () {

                i--;

                if (i < 0) i = $('.match').length - 1;

                $('.match').removeClass('highlighted');
                $('.match').eq(i).addClass('highlighted');
                
				
				$(window).scrollTop($('.match').eq(i).position().top);
            });




            if ($('.highlighted:first').length) { //if match found, scroll to where the first one appears
                $(window).scrollTop($('.highlighted:first').position().top);
            }
            return true;
        }
    }
    return false;
}

$(document).on('click', '.searchButtonClickText_h', function (event) {

    $(".highlighted").removeClass("highlighted");
    if (!searchAndHighlight($('.textSearchvalue_h').val())) {
        alert("No results found");
    }


});
});//]]> 