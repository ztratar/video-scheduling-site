import pystache
import os
from pystache.loader import Loader
from django.shortcuts import render_to_response
from django.template import RequestContext
from airety.utils import compress_cfg
from django.conf import settings
from django.core.context_processors import csrf

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

		c = {
			'innerBlock': pyRenderer.render_path('app/templates/'+page+'.mustache', pageVars),
			'javascriptBlock': javascript,
			'STATIC_URL': settings.STATIC_URL
		}
		c.update(csrf(request))

		return pyRenderer.render_path('app/templates/'+layout+'.mustache', c) + backboneTemplates
