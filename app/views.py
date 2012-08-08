import urllib2

from django.template import Context, loader
from django.http import HttpResponse
from django.contrib.auth import login, logout
from mongoengine.queryset import DoesNotExist
from querystring_parser import parser

from app.models import *
from app.helpers import get_current_user, model_encode 
from app.libs.getimageinfo import getImageInfo

from app.layout_manager import LayoutManager
renderer = LayoutManager()

# Views
def index(request):
	users = User.objects
	output = ', '.join([u.first_name for u in users])
	return HttpResponse(output)

def home(request):
	userFeed = User.objects
	output = renderer.render_with_layout(
		'layout',
		'index',
		{},
		{
			'withBackboneTemplates': True
		},
		request
	)
	return HttpResponse(output)

def logout_view(request):
	logout(request)
	return home(request)

def login_view(request):
    try:
        user = User.objects.get(fb_id=request.POST['id'])
        if user.check_access_token(request.POST['access_token']):
            user.backend = 'mongoengine.django.auth.MongoEngineBackend'
            login(request, user)
            request.session.set_expiry(60 * 60 * 24 * 30) # 1 month timeout
            return HttpResponse(model_encode(user), mimetype="application/json")
        else:
            return HttpResponse('login failed')
    except DoesNotExist:
		data = parser.parse(request.POST.urlencode())
		if not data.get('email'):
			data['email'] = str(data['id']) + '@facebook.com'
		if not data.get('username'):
			data['username'] = data['email']
		if not data.get('bio'):
			data['bio'] = ''
		user = User(
			username = data['email'],
			name = data['name'],
			first_name = data['first_name'],
			last_name = data['last_name'],
			fb_id = data['id'],
			fb_access_token = data['access_token'],
			fb_link = data['link'],
			fb_username = data['username'],
			bio = data['bio'],
			email = data['email'],
			timezone = data['timezone'],
			locale = data['locale'],
			gender = data['gender']
		)
		imgdata = urllib2.urlopen('https://graph.facebook.com/'+str(data['id'])+'/picture?type=large')
		image_type,width,height = getImageInfo(imgdata)
		user.picture_width = width
		user.picture_height = height
		user.save()
		if data.get('hometown'):
			user.add_property('location', data['hometown'], 650)
		if data.get('location'):
			user.add_property('location', data['location'], 750)
		for i in range(len(data['work'])):
			work_score = 200 * 3/(min(i,4)+1)
			user.add_property('work', data['work'][i], work_score)
		for i in range(len(data['education'])):
			user.add_property('school', data['education'][i], 680*(4+i)/4)
		for i in range(len(data['inspirational_people'])):
			user.add_property('inspirational_person', data['inspirational_people'][i], 200)
		user.set_default_featured_properties()
		return HttpResponse(model_encode(user), mimetype="application/json")
	#except Exception:
    #    return HttpResponse('unknown error')
