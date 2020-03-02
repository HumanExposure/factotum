import myDefault from './csrf_ajax.js'

export default function create_post (form_id) {
    var form = $(form_id)[0]
    return $.ajax({
        url : form.action, // the endpoint
        type : "POST", // http method
        data : create_post_data(form_id), // data sent with the post request

        // handle a successful response
        success : function() {

        },

        // handle a non-successful response
        error : function(response) {
            // Declarations
            var input
            var element
            var error

            // clear previous form errors
            var elements = document.getElementsByClassName("is-invalid")
            for (element of elements) {
                element.classList.remove("is-invalid")
            }
            var elements = document.getElementsByClassName("invalid-feedback")
            for (element of elements) {
                console.log(element)
                element.parentNode.removeChild(element)
            }

            // add new form errors
            for (input of form)
            {
                if (input.name in response.responseJSON) {
                    input.classList.add("is-invalid")
                    for (error of response.responseJSON[input.name])
                    {
                        input.outerHTML += "<div class=\"invalid-feedback\">" + error +"</div>"
                    }
                }
            }
        }
    });

    function create_post_data(form_id) {
        var array = {}
        var row
        for (row of $(form_id).serializeArray()) {
            if (row.name !== "csrfmiddlewaretoken") {
                array[row.name] = row.value
            }
        }
        return array
    }
}
