from django.template import Context, loader
from django.http import HttpResponse

from app.models import *

from app.layout_manager import LayoutManager
renderer = LayoutManager()

def index(request):
	users = User.objects
	output = ', '.join([u.first_name for u in users])
	return HttpResponse(output)

def home(request):
	users = User.objects
	output = renderer.render_with_layout(
		'layout',
		'index',
		{
			'test': 'me'	
		},
		{
			'withBackboneTemplates': True
		},
		request
	)
	return HttpResponse(output)
