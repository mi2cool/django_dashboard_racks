from django.http import HttpResponse, HttpResponseRedirect


def download_report(request, rack_pk):
    next = request.GET.get('next', '/')
    return HttpResponseRedirect(next)
