from django.template import Context, loader
from django.http import HttpResponse
from django.contrib.auth import login
from mongoengine.queryset import DoesNotExist
from querystring_parser import parser

from app.models import *
from app.helpers import get_current_user, model_encode 

from app.layout_manager import LayoutManager
renderer = LayoutManager()

# Views
def index(request):
	users = User.objects
	output = ', '.join([u.first_name for u in users])
	return HttpResponse(output)

def home(request):
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

def login_view(request):
    try:
        user = User.objects.get(fb_id=request.POST['id'])
        if user.check_access_token(request.POST['access_token']):
            user.backend = 'mongoengine.django.auth.MongoEngineBackend'
            login(request, user)
            request.session.set_expiry(60 * 60 * 24 * 30) # 1 month timeout
            return HttpResponse(model_encode(user))
        else:
            return HttpResponse('login failed')
    except DoesNotExist:
		data = parser.parse(request.POST.urlencode())
		user = User(
			username = data['email'],
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
		user.save()
		user.add_property('location', data['hometown'], 800)
		user.add_property('location', data['location'], 900)
		for i in range(len(data['work'])):
			work_score = 200 * (min(i,4)+1)/2
			user.add_property('work', data['work'][i], work_score)
		for i in range(len(data['education'])):
			user.add_property('school', data['education'][i], 680)
		for i in range(len(data['inspirational_people'])):
			user.add_property('inspirational_person', data['inspirational_people'][i], 200)
		return HttpResponse(model_encode(user))
	#except Exception:
    #    return HttpResponse('unknown error')
