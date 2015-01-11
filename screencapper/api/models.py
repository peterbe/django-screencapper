from django.db import models
from django.utils import timezone

from jsonfield.fields import JSONField


class Submission(models.Model):
    url = models.URLField()
    callback_url = models.URLField()
    submitted = models.DateTimeField(default=timezone.now)
    number = models.IntegerField(default=10)
    post_files = models.BooleanField(default=False)
    post_files_individually = models.BooleanField(default=False)
    post_file_name = models.CharField(max_length=100, default='files')
    download = models.BooleanField(default=False)
    stats = JSONField()


class CallbackResponse(models.Model):
    submission = models.ForeignKey(Submission)
    content = models.TextField()
    status_code = models.IntegerField()
