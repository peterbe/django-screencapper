from django.db import models
from django.utils import timezone


class Picture(models.Model):
    file = models.ImageField()
    url = models.URLField()
    uploaded = models.DateTimeField(default=timezone.now)
