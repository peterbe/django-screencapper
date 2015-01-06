import hashlib
import os

from django.db import models
from django.utils import timezone


def upload_to(instance, filename):
    now = timezone.now()
    path = os.path.join(
        'pictures',
        now.strftime('%Y/%m/%d'),
        hashlib.md5(instance.url).hexdigest()[:12],
        filename
    )
    return path


class Picture(models.Model):
    file = models.ImageField(upload_to=upload_to)
    url = models.URLField()
    uploaded = models.DateTimeField(default=timezone.now)
