import string
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
		return HttpResponse(model_encode(users), mimetype="application/json")
	except DoesNotExist:
		return HttpResponse('Cannot get your feed. Sorry!')

def requests_create(request):
	try:
		if (not 'user_id' in request.POST or
				not 'times' in request.POST or
				not 'message' in request.POST):
			return HttpResponse('Missing params')

		returnArray = []
		
		user = get_current_user(request)
		user2 = User.objects(id=request.POST['user_id'])[0]

		for time in request.POST['times']:
			r = Request(
				request_from = user,
				request_to = user2,
				start_datetime = datetime.utcfromtimestamp(time['start']),
				end_datetime = datetime.utcfromtimestamp(time['end']),
				message = request.POST['message']
			)
			r.save()
			returnArray.append(r)

		user.requests_out.append(returnArray);
		user2.requests_in.append(returnArray);

		return HttpResponse(model_encode(returnArray))
	except DoesNotExist:
		return HttpResponse('Users not found')

# Convert to UTC slots and then save
def user_availability_create(request):
	#try:
	data = parser.parse(request.POST.urlencode())
	user = get_current_user(request)
	if data.get('availability'):
		availability_raw = data['availability']['']
	else:
		availability_raw = []
	availability = []
	if not isinstance(availability_raw, list):
		availability_raw = [availability_raw]
	for available_raw_item in availability_raw:
		avail_data = string.split(available_raw_item, '_')
		print avail_data
		if avail_data[1] == 'morning':
			time_array = [16, 18, 20, 22]
		elif avail_data[1] == 'afternoon':
			time_array = [24, 26, 28, 30]
		elif avail_data[1] == 'night':
			time_array = [32, 34, 36, 38]
		elif avail_data[1] == 'late-night':
			time_array = [40, 42, 44]
		elif avail_data[1] == 'night-owl':
			time_array = [46, 48, 50]
		for time in time_array:
			availability.append({
				'day': int(avail_data[0]),
				'start_time': int(time),
				'end_time': int(time) + 2
			})

	availability_array = []
	for available_slot in availability:
		newSlot = available_slot
		newSlot['start_time'] -= user.timezone * 2
		newSlot['end_time'] -= user.timezone * 2
		if newSlot['start_time'] < 0:
			newSlot['day'] = newSlot['day'] - 1
			newSlot['start_time'] = 48 + newSlot['start_time']
		if newSlot['end_time'] < 0:
			newSlot['end_time'] = 48 + newSlot['end_time']
		if newSlot['start_time'] > 47:
			newSlot['start_time'] = newSlot['start_time'] - 48
			newSlot['day'] = newSlot['day'] + 1
		if newSlot['end_time'] > 47:
			newSlot['end_time'] = newSlot['end_time'] - 48
		if newSlot['day'] < 0:
			newSlot['day'] = 7 + newSlot['day']
		if newSlot['day'] > 6:
			newSlot['day'] = newSlot['day'] - 7
		avail_document = UserAvailability(
			day = newSlot['day'],
			start_time = newSlot['start_time'],
			end_time = newSlot['end_time']
		)
		availability_array.append(avail_document)
	user.availability = availability_array
	user.save()
	return HttpResponse(model_encode(user.availability_tz()), mimetype="application/json")
	#except Exception:
	#	return HttpResponse('Could not save availability')

def user_availability(request,uid):
	try:
		returnArray = []

		user = User.objects(id=uid)[0]
		current_user = get_current_user(request)
		
		today = datetime.utcnow()

		# Get all chats schedule by both users. Throw out times that overlap
		chats_this_week = []
		chats_this_week.append(user.chats_this_week())
		chats_this_week.append(current_user.chats_this_week())

		# Get current users outgoing requests. Do not allow double requests at
		# a time
		c_user_out_requests = current_user.outgoing_requests_this_week()

		# Get current users incoming requests. Add as meta data so users do not
		# double book.
		c_user_in_requests = current_user.incoming_requests_this_week()

		# Get target users incoming requests. Add as meta data to show how
		# competitive a certain time spot is.
		user_in_requests = user.incoming_requests_this_week()

		# Get target users outgoing requests. Do not allow users to stack
		# these as it may lead to a confusing cycle.
		user_out_requests = user.outgoing_requests_this_week()

		# Get next 7 days availability times as datetime UTC objects
		user_availability = user.availability_this_week()

		# Move through all the users' usually available slots and find the
		# times that will actually work this week.	
		for available_slot in user_availability:
			
			additionalMetaData = {
				time: available_slot,
				time_slot_competition: 0,
				request_overlap: []
			}

			for chat in chats_this_week:
				if chat.start_datetime == available_slot:
					break
			else:
				continue

			for chat_request in c_user_out_requests:
				if chat_request.start_datetime == available_slot:
					break
			else:
				continue

			for chat_request in user_out_requests:
				if chat_request.start_datetime == available_slot:
					break
			else:
				continue

			for chat_request in c_user_in_requests:
				if chat_request.start_datetime == available_slot:
					additionalMetaData.request_overlap.append(chat_request)

			for chat_request in user_in_requests:
				if chat_request.start_datetime == available_slot:
					additionalMetaData.time_slot_competition += 1
			
			returnArray.append(additionalMetaData)

	except Exception as inst:
		return HttpResponse('An error occured: '+str(inst.args))


