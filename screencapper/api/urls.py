from django.conf.urls import patterns, include, url

from screencapper.api import views

urlpatterns = patterns('',
    url(r'^transform$', views.transform, name='transform'),
)
