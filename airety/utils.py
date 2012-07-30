# utils.py

import os
from urllib2 import urlopen
from simplejson import loads

def compress_cfg(static_url, static_root, dir, paths):
	output = ''
	static_url += dir
	static_root += dir
	for p in paths:
		if p.endswith('/'):
			output = include_tree(static_url, static_root, p, output)
		else:
			output += include_file(static_url, static_root, p)
	return output

def include_tree(static_url, static_root, dir, output):
	files = os.listdir(static_root + dir)
	files.sort()
	output += ''
	subdirlist = []
	for f in files:
		fileloc = dir + f
		if os.path.isfile(os.path.join(static_root, fileloc)):
			output += include_file(static_url, static_root, fileloc) 	
		else:
			subdirlist.append(fileloc + '/')
	for subdir in subdirlist:
		output = include_tree(static_url, static_root, subdir, output)
	return output

def include_file(static_url, static_root, pathtofile):
	return '<script type="text/javascript" src="' + static_url + pathtofile +'"></script>\n  '

def get_data_from_url(url, access_token):
	return loads(urlopen(url+'?access_token='+access_token).read())
