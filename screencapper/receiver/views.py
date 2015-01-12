import json
import urllib2
import os
from pprint import pprint

from django import http
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

from screencapper.receiver.models import Picture
from screencapper.api.models import Submission


@csrf_exempt
def home(request):
    if request.method == 'POST':
        # print "POST"
        # print request.POST.items()
        print "STATS"
        pprint(json.loads(request.POST['stats']))

        # print repr(request.POST)
        video_url = request.POST['url']
        if request.POST.getlist('urls'):
            # print "LIST:"
            # print request.POST.getlist('urls')
            for url in request.POST.getlist('urls'):
                # print "\tURL:", url
                # http://stackoverflow.com/a/2141823/205832
                img_temp = NamedTemporaryFile(delete=True)
                img_temp.write(urllib2.urlopen(url).read())
                img_temp.flush()
                filename = os.path.basename(url)
                picture = Picture(url=video_url)
                picture.file.save(filename, File(img_temp))
                # print "\t", repr(picture)
                # print "\t", picture.id
        else:
            # print "FILES"
            # print request.FILES
            # print repr(request.FILES.getlist('file'))
            for f in request.FILES.getlist('file'):
                # print type(f)
                # print repr(f)
                # print dir(f)
                # print f.read()
                # print "name:", repr(f.name)
                picture = Picture(url=video_url)
                # print dir(picture.file)
                # print dir(picture.file.field)
                # print picture.file.field.upload_to(picture, f.name)
                picture.file.save(f.name, f)
                # break
                # print repr(picture)
                # print picture.file.url
                # print picture.file.path
                # print

            # raise NotImplementedError

        return http.HttpResponse('OK\n')

    current_url = request.build_absolute_uri()
    context = {
        'pictures': Picture.objects.all().order_by('-uploaded'),
        'current_url': current_url,
        'submissions': Submission.objects.all().order_by('-submitted'),
    }
    for x in context['submissions']:
        print repr(x.stats)
    return render(request, 'home.html', context)
