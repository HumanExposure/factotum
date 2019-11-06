import base64
from elastic.search import run_query, FACETS
from django.shortcuts import render

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect

from elastic.search import run_query, FACETS
from elastic.models import QueryLog


def search_model(request, model, template_name="search/base.html"):
    page = request.GET.get("page", 1)
    encoded_q = request.GET.get("q", "")
    decoded_q = base64.b64decode(encoded_q).decode("unicode_escape")
    # Ensure querystring is valid
    max_q_size = QueryLog._meta.get_field("query").max_length
    if len(decoded_q) > max_q_size:
        err_msg = "Please limit your query to %d characters." % max_q_size
        messages.error(request, err_msg)
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    # Base64 decode the facets
    facets = {}
    for f in FACETS:
        if f in request.GET:
            facet_strs = []
            for s in request.GET[f].split(","):
                try:
                    facet_strs.append(base64.b64decode(
                        s).decode("unicode_escape"))
                except:
                    pass
            if facet_strs:
                facets[f] = facet_strs
    # Log the initial query
    # The default model is "product", the default page is 1, and the default has no facets.
    # Only this initial query will be logged.
    if page == 1 and model == "product" and not facets:
        user_id = request.user.pk if request.user else None
        QueryLog.objects.create(
            query=decoded_q, application=QueryLog.FACTOTUM, user_id=user_id
        )
    result = run_query(decoded_q, model, size=10, facets=facets, page=page)
    context = {
        "encoded_q": encoded_q,
        "decoded_q": decoded_q,
        "result": result,
        "model": model,
        "faceted": bool(facets),
    }
    return render(request, template_name, context)
