from django.template import Context, loader
from django.http import HttpResponse
from django.contrib.auth import login
from mongoengine.queryset import DoesNotExist
from querystring_parser import parser

from app.models import *
from app.helpers import get_current_user, model_encode 

# api

def feed(request):
	try:
		users = User.objects
		return HttpResponse(model_encode(users))
	except DoesNotExist:
		return HttpResponse('Cannot get your feed. Sorry!')
