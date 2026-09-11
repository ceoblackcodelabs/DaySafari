from django.shortcuts import render
from django.template import loader
from django.http import HttpResponseServerError

def custom_404(request, exception):
    return render(request, "pages/404.html", status=404)

def custom_500(request):
    # Deliberately bypass render()/RequestContext here: render() still runs
    # every context processor (including Home.context_processors.ads_context,
    # which hits the DB) even on an error page, and if THAT throws too we'd
    # have an error handler that itself crashes, which is how you end up back
    # at Django's bare hardcoded fallback page with no traceback anywhere.
    # Not passing `request` to render() below means context processors are
    # skipped entirely.
    template = loader.get_template("pages/500.html")
    return HttpResponseServerError(template.render({}))