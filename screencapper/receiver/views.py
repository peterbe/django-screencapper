from django.shortcuts import render

from screencapper.receiver.models import Picture


def home(request):
    if request.method == 'POST':
        print "POST"
        print request.POST.items()
        raise NotImplementedError

    context = {
        'pictures': Picture.objects.all().order_by('-uploaded')
    }
    return render(request, 'home.html', context)
