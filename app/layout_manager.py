import pystache
import os
from pystache.loader import Loader
from django.shortcuts import render_to_response
from django.template import RequestContext
from airety.utils import compress_cfg
from django.conf import settings

pyRenderer = pystache.Renderer()
pyLoader = Loader()

jsfiles = [ 'lib/jquery.js',
			'lib/underscore.js',
			'lib/json2.js',
			'lib/mustache.js',
			'lib/backbone.js',
			'lib/lazyload.js',
			'init.js',
			'backbone/',
			'run.js', ]
javascript = compress_cfg(settings.STATIC_URL, settings.STATIC_ROOT, 'js/', jsfiles)

class LayoutManager(object):

	def get_backbone_templates(self, include_backbone_templates):
		if include_backbone_templates:
			return pyLoader.read('app/templates/backbone_templates.mustache')
		else:
			return ''
	
	def render_with_layout(self, layout, page, pageVars, options, request):
		backboneTemplates = self.get_backbone_templates(options['withBackboneTemplates'])

		if 'renderLayoutWithPython' in options:
			renderLayoutWithPython = options['renderLayoutWithPython']
		else:
			renderLayoutWithPython = False

		if renderLayoutWithPython:
			return render_to_response(layout+'.mustache', {
				'innerBlock': pyRenderer.render_path('app/templates/'+page+'.mustache', pageVars),
				'javascriptBlock': javascript,
				'STATIC_URL': settings.STATIC_URL
			}, context_instance=RequestContext(request))
		else:
			return pyRenderer.render_path('app/templates/'+layout+'.mustache',{
				'innerBlock': pyRenderer.render_path('app/templates/'+page+'.mustache', pageVars),
				'javascriptBlock': javascript,
				'STATIC_URL': settings.STATIC_URL
			}) + backboneTemplates

