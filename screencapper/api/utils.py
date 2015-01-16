import urlparse

import requests


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
    """XXX there is probably a much better way to do this using something
    already in django. Like the stuff that URLField uses."""
    parsed = urlparse.urlparse(url)
    if parsed.netloc and parsed.path:
        if parsed.scheme in ('http', 'https'):
            return True
    return False
