import requests

from django import forms

from .models import Submission


class TransformForm(forms.ModelForm):
    class Meta:
        model = Submission
        exclude = ('submitted', 'stats')

    def __init__(self, *args, **kwargs):
        super(TransformForm, self).__init__(*args, **kwargs)
        self.fields['post_file_name'].required = False

    def clean_url(self):
        url = self.cleaned_data['url'].strip()
        # it must be possible to do a HEAD and get a video content type
        head = requests.head(url)
        redirects = 0
        while head.status_code in (301, 302):
            if redirects > 3:
                raise forms.ValidationError(
                    "{0} causes too many redirects".format(url)
                )
            redirects += 1
            url = head.headers['Location']
            head = requests.head(url)
        content_type = head.headers['Content-Type']
        if not content_type.startswith('video/'):
            raise forms.ValidationError("Not a video/ content type")
        return url
