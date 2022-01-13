/**
* Created by Tobias on 12.02.2019
*/

$(function () {

        // using jQuery
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function switch_page() {
        goals_reload_data( $(this).data('page') );
    }

    function switch_pageselect() {
        console.log($(this).val());
        goals_reload_data( $(this).val() );
    }

    function goals_reload_data(page) {
        var theform = document.getElementById("facet-form");
        var formData = new FormData(theform);
        // formData.append('csrfmiddlewaretoken', '{{ csrf_token }}');
        if (page==-1) {
            formData.append('nopaging', 1);
        } else {
            formData.append('page', page);
        }
        //fd.append("CustomField", "This is some extra data");
        $.ajax({ // reload the data with an ajax request containing form data and csrf token
          url: "{% url 'goals_data' %}",
          type: "POST",
          data: formData,
          processData: false,  // tell jQuery not to process the data
          contentType: false,   // tell jQuery not to set contentType
          cache: false,
          error: function () { $('#goals-content').html("<h1>Fehler: Daten konnten nicht abgerufen werden.</h1>"); window.scrollTo(0,0);},
          success: function(data) { $('#goals-content').html(data); window.scrollTo(0,0);}
        });
    }

    // Django CSRF protection for AJAX calls
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    var csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    $('#facet-form').change(goals_reload_data);
    $('#facet-form').on("submit", function (event) {event.preventDefault(); goals_reload_data(); });
    $('#goals-content').on("click", ".paginator", switch_page);
    $('#goals-content').on("change", ".pageselector", switch_pageselect);
    $('#goals-content').on("click", ".nopaging", function () { goals_reload_data(-1); });

    //$(document).on("click", "button.delete-wordform", delete_wordform);
    //$(document).on("click", ".addcomp", addcomp_click);
    $(document).ajaxStart(function() { $( "#loading" ).show(); });
    $(document).ajaxStop(function() { $( "#loading" ).hide(); });
    goals_reload_data();
});
