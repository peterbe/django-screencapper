import os
import subprocess
import re
import datetime
import shutil
import tempfile
import contextlib
import urlparse
import glob
import hashlib

from django import http
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

import requests
from jsonview.decorators import json_view

from .downloader import download

from alligator import Gator

gator = Gator(settings.ALLIGATOR_CONN)


@contextlib.contextmanager
def make_temp_dir(url):
    dir_ = tempfile.mkdtemp('screencapper')
    yield dir_
    print "DELETING", dir_
    shutil.rmtree(dir_)


def get_duration(filepath):
    process = subprocess.Popen(
        ['ffmpeg', '-i', filepath],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    stdout, stderr = process.communicate()
    matches = re.search(
    r"Duration:\s{1}(?P<hours>\d+?):(?P<minutes>\d+?):(?P<seconds>\d+\.\d+?),",
        stdout,
        re.DOTALL
    ).groupdict()
    hours = float(matches['hours'])
    minutes = float(matches['minutes'])
    seconds = float(matches['seconds'])

    total = 0
    total += 60 * 60 * hours
    total += 60 * minutes
    total += seconds
    return total


def _format_time(seconds):
    m = seconds / 60
    s = seconds % 60
    h = m / 60
    m = m % 60
    return '%02d:%02d:%02d' % (h, m,s)


def _mkdir(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)
        if tail:
            os.mkdir(newdir)


def extract_pictures(filepath, duration, number, output):
    incr = float(duration) / number
    seconds = 0
    number = 0
    while seconds < duration:
        number += 1
        output_each = output.format(number)
        command = [
            'ffmpeg',
            '-ss',
            _format_time(seconds),
            '-y',
            '-i',
            filepath,
            '-vframes',
            '1',
            output_each,
        ]
        print ' '.join(command)
        out, err = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).communicate()
        seconds += incr


def check_url(url):
    url = url.strip()
    if not valid_url(url):
        return
    head = requests.head(url)
    if head.status_code == 302:
        url = head.headers['location']
        return check_url(url)
    if head.status_code == 200:
        return url


def valid_url(url):
    parsed = urlparse.urlparse(url)
    if parsed.netloc and parsed.path:
        if parsed.scheme in ('http', 'https'):
            return True
    return False


def download_and_save(url, number, callback_url):
    head = requests.head(url, allow_redirects=True)
    content_type = head.headers['Content-Type']
    with make_temp_dir(url) as temp_dir:
        filename = hashlib.md5(url).hexdigest()[:12]
        if content_type == 'video/mp4':
            filename += '.mp4'
        elif content_type == 'video/webm':
            filename += '.webm'
        else:
            call_back_error(
                callback_url,
                error="Unrecognized content type %r" % content_type
            )
        destination = os.path.join(temp_dir, filename)
        response = download(url, destination)
        if response['code'] == 200:
            extract_and_call_back(
                destination,
                number,
                callback_url
            )


def extract_and_call_back(video_url, number, callback_url):
    duration = get_duration(video_url)
    destination = os.path.join(
        settings.MEDIA_ROOT,
        'screencaps',
        datetime.datetime.utcnow().strftime('%Y/%m/%d'),
        hashlib.md5(video_url).hexdigest()[:12]
    )
    _mkdir(destination)
    output = os.path.join(
        destination,
        'screencap-{0:03d}.jpg'
    )
    extract_pictures(
        video_url,
        duration,
        number,
        output
    )
    files = sorted(glob.glob(
        os.path.join(destination, 'screencap-*.jpg')
    ))

    callback(callback_url, files)


def callback(url, files):
    print "FILES"
    print files
    # print "MEDIA_ROOT", settings.MEDIA_ROOT
    urls = [
        settings.MEDIA_URL +
        x.replace(settings.MEDIA_ROOT + '/', '')
    ]
    data = {
        'urls': urls,
    }
    response = requests.post(
        url,
        data
    )
    print response.status_code


@csrf_exempt
@json_view
def transform(request):
    url = request.POST['url']
    callback_url = request.POST['callback_url']
    number = int(request.POST.get('number', 15))

    checked_url = check_url(url)
    if not checked_url:
        raise BadRequest(url)  # XXX

    assert number > 0 and number < 100, number
    assert valid_url(callback_url), callback_url

    gator.task(
        download_and_save,
        checked_url, number, callback_url
    )

    return http.HttpResponse('OK\n', status=201)
    # context = {
    #     'urls': [],
    #     'time': {
    #         'download': download_time,
    #         'transform': transform_time,
    #         'total': download_time + transform_time,
    #     },
    # }
    # return context
