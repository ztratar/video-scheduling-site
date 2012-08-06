from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('app.views',
    # Examples:
    url(r'^$', 'home'),
	url(r'^login$', 'login_view'),
	url(r'^logout$', 'logout_view'),
    # url(r'^airety/', include('airety.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('app.api',
	url(r'^api/feed$', 'feed'),
	url(r'^api/user_availability_create$', 'user_availability_create'),
	url(r'^api/users/(?P<uid>[0-9a-zA-Z]+)/open_schedule$', 'user_open_schedule')
)
