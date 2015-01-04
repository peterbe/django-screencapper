from django.conf.urls import patterns, include, url

from screencapper.receiver import views


urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
)
