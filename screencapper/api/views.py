import json
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
import time
import stat
from pprint import pprint

from django import http
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.template.defaultfilters import filesizeformat as _filesizeformat
from django.contrib.sites.shortcuts import get_current_site

import requests
from jsonview.decorators import json_view
from alligator import Gator

from .downloader import download
from .forms import TransformForm
from .models import Submission, CallbackResponse

gator = Gator(settings.ALLIGATOR_CONN)


def filesizeformat(bytes):
    return _filesizeformat(bytes).replace(u'\xa0', ' ')


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
        # print ' '.join(command)
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


def download_and_save(url, callback_url, options):
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
        print "About to download"
        print "\t", url
        print "To"
        print "\t", destination
        print
        t0 = time.time()
        response = download(url, destination)
        t1 = time.time()
        print "Took", t1 - t0, "seconds to download",
        size = os.stat(destination)[stat.ST_SIZE]
        print filesizeformat(size)
        stats = {
            'time': {
                'download': round(t1 - t0, 4)
            },
            'size': size,
            'size_human': filesizeformat(size),
        }
        if response['code'] == 200:
            extract_and_call_back(
                destination,
                callback_url,
                options,
                stats
            )
        else:
            raise NotImplementedError(response)



def extract_and_call_back(video_url, callback_url, options, stats):
    submission = Submission.objects.get(id=options['submission'])
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
    t0 = time.time()
    extract_pictures(
        video_url,
        duration,
        options['number'],
        output
    )
    t1 = time.time()

    files = sorted(glob.glob(
        os.path.join(destination, 'screencap-*.jpg')
    ))
    print "Took", t1 - t0, "seconds to extract", len(files), "pictures"
    stats['time']['transform'] = round(t1 - t0, 4)
    submission.stats = stats
    submission.save()
    callback(callback_url, files, options, stats)


def callback(url, files, options, stats):
    submission = Submission.objects.get(id=options['submission'])

    print "OPTIONS"
    print options
    print "FILES"
    print files
    stats['time']['total'] = round(
        sum(stats['time'].values())
    )
    data = {
        'url': options['url'],
        'stats': json.dumps(stats),
    }
    if options['post_files']:

        if options['post_files_individually']:
            for file in files:
                gator.task(
                    send_individual_file,
                    url,
                    file,
                    data,
                    options
                )
            return
        else:
            print "Posting files..."
            pprint(data)
            print "To..."
            print url

            response = requests.post(
                url,
                files=make_multiple_files(options['post_file_name'], files),
                data=data
            )
            CallbackResponse.objects.create(
                submission=submission,
                content=response.content,
                status_code=response.status_code
            )
            for f in files:
                print "Deleting", f
                os.remove(f)
    else:
        # then post the URLs
        base_url = '%s://%s' % (options['protocol'], options['domain'])
        urls = [
            base_url +
            settings.MEDIA_URL +
            x.replace(settings.MEDIA_ROOT + '/', '')
            for x in files
        ]
        data['urls'] = urls
        print "Posting urls..."
        pprint(data)
        print "To..."
        print url
        response = requests.post(
            url,
            data
        )
        CallbackResponse.objects.create(
            submission=submission,
            content=response.content,
            status_code=response.status_code
        )
    print "Response code..."
    print response.status_code


def send_individual_file(url, file, data, options):
    submission = Submission.objects.get(id=options['submission'])
    print "Posting file..."
    pprint(data)
    print "To..."
    print url
    response = requests.post(
        url,
        files=make_multiple_files(options['post_file_name'], [file]),
        data=data
    )
    CallbackResponse.objects.create(
        submission=submission,
        content=response.content,
        status_code=response.status_code
    )
    print response.status_code


def make_multiple_files(name, files):
    return [
        (
            name,
            (
                os.path.basename(f),
                open(f, 'rb'),
                'image/jpeg'
            )
        )
        for f in files
    ]


@csrf_exempt
@json_view
def transform(request):
    form = TransformForm(request.POST)
    if not form.is_valid():
        return http.HttpResponseBadRequest(
            json.dumps(dict(form.errors)),
            content_type='application/json'
        )

    submission = form.save()
    url = submission.url
    callback_url = submission.callback_url
    number = submission.number
    post_files = submission.post_files
    post_file_name = submission.post_file_name or 'file'
    post_files_individually = submission.post_files_individually
    download = submission.download

    checked_url = check_url(url)
    if not checked_url:
        raise http.HttpResponseBadRequest(url)

    assert number > 0 and number < 100, number
    assert valid_url(callback_url), callback_url

    options = {
        'number': number,
        'url': url,
        'post_files': bool(post_files),
        'post_files_individually': bool(post_files_individually),
        'post_file_name': post_file_name,
        'domain': get_current_site(request).domain,
        'protocol': request.is_secure() and 'https' or 'http',
        'submission': submission.id,
    }
    if download:
        gator.task(
            download_and_save,
            checked_url, callback_url,
            options
        )
    else:
        # don't bother downloading, just do it on the remote file
        stats = {
            'time': {},
        }
        gator.task(
            extract_and_call_back,
            url,
            callback_url,
            options,
            stats,
        )

    return http.HttpResponse('OK\n', status=201)
