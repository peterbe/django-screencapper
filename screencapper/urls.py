from django.conf.urls import patterns, include, url
# from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'screencapper.base.views.home', name='home'),
    url(r'v1/', include('screencapper.api.urls')),
    url(r'receiver/', include('screencapper.receiver.urls')),

    # url(r'^admin/', include(admin.site.urls)),
)
