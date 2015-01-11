from django import forms


class TransformForm(forms.Form):
    url = forms.URLField()
    callback_url = forms.URLField()
    number = forms.IntegerField(required=False)
    post_files = forms.BooleanField(required=False)
    post_files_individually = forms.BooleanField(required=False)
    post_file_name = forms.CharField(required=False)
    download = forms.BooleanField(required=False)
