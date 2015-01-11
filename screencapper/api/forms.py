from django import forms

from .models import Submission


class TransformForm(forms.ModelForm):
    class Meta:
        model = Submission
        exclude = ('submitted', 'stats')

    def __init__(self, *args, **kwargs):
        super(TransformForm, self).__init__(*args, **kwargs)
        self.fields['post_file_name'].required = False
