import bson
import bson.json_util
import re

from app.models import *

def model_encode(obj):
	keys = bson.json_util._json_convert(obj)
	returnObj = {}
	for key in keys:
		returnObj[key] = obj[key]
	rawJson = bson.json_util.dumps(returnObj)
	crapRemovedJson = re.sub(r'{"\$oid": "([a-zA-Z0-9]*)"}',
							 r'"\1"',
							 rawJson)
	crapRemovedJson = re.sub(r'{"\$date": ([0-9]*)}',
							 r'\1',
							 crapRemovedJson)
	return crapRemovedJson
def get_current_user(request):
	user = User.objects(id=str(request.session['_auth_user_id']))[0]
	return user

