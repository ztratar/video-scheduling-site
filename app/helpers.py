import bson
import bson.json_util
import re
import mongoengine
import unicodedata
import json

from app.models import *

def model_encode(obj):
	returnObj = model_encode_helper(obj)
	rawJson = bson.json_util.dumps(returnObj)
	crapRemovedJson = re.sub(r'{"\$oid": "([a-zA-Z0-9]*)"}',
							 r'"\1"',
							 rawJson)
	crapRemovedJson = re.sub(r'{"\$date": ([0-9]*)}',
							 r'\1',
							 crapRemovedJson)
	return crapRemovedJson

def model_encode_helper(obj):
	if (isinstance(obj, mongoengine.queryset.QuerySet)
			or isinstance(obj, list)):
		output = []
		for model in obj:
			output.append(model_encode_helper(model))
		return output
	else:
		keys = bson.json_util._json_convert(obj)
		returnObj = {}
		if keys != bson.json_util.object_hook(keys):
			for key in keys:
				returnObj[key] = keys
		else:
			for key in keys:
				if (isinstance(obj[key], mongoengine.queryset.QuerySet)
						or isinstance(obj[key], list)):
					returnObj[key] = model_encode_helper(obj[key])
				else:
					returnObj[key] = obj[key]
		return returnObj

def get_current_user(request):
	user = User.objects(id=str(request.session['_auth_user_id']))[0]
	return user

def remove_accents(data):
    return ''.join(x for x in unicodedata.normalize('NFKD', data) if x in string.ascii_letters).lower()
