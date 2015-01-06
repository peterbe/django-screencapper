import shutil

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from screencapper.receiver.models import Picture


class Command(BaseCommand):
    help = 'Delete them all!'

    def handle(self, *args, **options):
        Picture.objects.all().delete()
        # print settings.MEDIA_ROOT
        shutil.rmtree(settings.MEDIA_ROOT)
