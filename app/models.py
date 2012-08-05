from django.db import models
from mongoengine import *
from datetime import datetime
from mongoengine.django.auth import User as MongoUser
from airety.utils import get_data_from_url

import OpenTokSDK
tok_api = '14712672'
tok_secret = '3da704cbbda26bb38e50d430d0fecfd7ffc0269f'


# UserLinkProperty
#   A specific common trait among users.
class UserProperty(Document):

	name = StringField(required=True)
	fb_id = IntField()
	property_type = StringField(required=True)
	latlong = GeoPointField()
	thumburl = StringField()

class UserPropertyLink(Document):

	user = ReferenceField('User', required=True)
	user_property_id = ObjectIdField(required=True)
	property_type = StringField(required=True)
	affinity = IntField(required=True, default=200)
	affinity_actions = IntField(default=0)

class UserAvailability(EmbeddedDocument):

	# Day: 0 = Monday, ..., 6 = Sunday 
	day = IntField(required=True)

	# Times: 0 = 12AM, 1 = 12:30AM, 2 = 1AM, ..., 47 = 11:30PM
	start_time = IntField(required=True)
	end_time = IntField(required=True)

class Request(Document):

	request_from = ReferenceField('User', required=True)
	request_to = ReferenceField('User', required=True)
	
	start_datetime = DateTimeField(required=True)
	end_datetime = DateTimeField(required=True)

	request_to_confirm = BooleanField(required=True, default=False)
	request_form_confirm = BooleanField(required=True, default=False)
	
	message = StringField(max_length=300)

class User(MongoUser):

	def __unicode__(self):
		return self.getFullName()

	name = StringField(required=True)
	first_name = StringField(required=True)
	last_name = StringField(required=True)
	email = StringField(required=True)
	timezone = IntField(required=True)

	fb_id = IntField(required=True)
	fb_username = StringField()
	fb_link = StringField()
	fb_access_token = StringField(required=True)
	is_admin = BooleanField(required=True, default=False)

	created_at = DateTimeField(required=True, default=datetime.utcnow())
	edited_at = DateTimeField(required=True, default=datetime.utcnow())

	gender = StringField()
	bio = StringField()
	picture_url = StringField()
	picture_width = IntField()
	picture_height = IntField()
	thumb_url = StringField()

	has_availability = BooleanField(default=False)
	availability = ListField(EmbeddedDocumentField(UserAvailability))
	requests_out = ListField(ReferenceField('Request'))
	requests_in = ListField(ReferenceField('Request'))

	chats = ListField(ReferenceField('Chat'))

	# Track
	sign_in_count = IntField(default=0)
	last_sign_in_at = DateTimeField(default=datetime.utcnow())
	schedule_viewed_count = IntField(default=0)
	chat_out_request_count = IntField(default=0)
	chat_out_request_accepted_count = IntField(default=0)
	chat_in_request_count = IntField(default=0)
	chat_in_request_accepted_count = IntField(default=0)

	def property_links(self):
		return UserPropertyLink.objects(user=self)
	
	def getFullName(self):
		return self.first_name + ' ' + self.last_name

	def workplaces(self):
		return UserLinkProperty.objects(id__in=self.property_links__user_property_id)

	def schools(self):
		return UserLinkProperty.objects(id__in=self.property_links__user_property_id)

	def locations(self):
		return UserLinkProperty.objects(id__in=self.property_links__user_property_id)

	def check_access_token(self, access_token):
		# todo: check access token
		try:
			self.fb_access_token = access_token
			self.save()
			return True
		except Exception:
			return False

	def chats_this_week(self):
		chats = Chat.objects(
			(Q(user_from = self) | Q(user_to = self))
			&
			Q(start_datetime__gt = datetime.utcnow())
			&
			Q(start_datetime__lt = datetime.utcnow() + datetime.timeDelta(weeks=1))
		)
		return chats

	def incoming_requests_this_week(self):
		requests = Requests.objects(
			Q(request_to = self)
			&
			Q(start_datetime__gt = datetime.utcnow())
			&
			Q(start_datime__lit = datetime.utcnow() + datetime.timeDelta(weeks=1))
		)
		return requests

	def outgoing_requests_this_week(self):
		requests = Requests.objects(
			Q(request_from = self)
			&
			Q(start_datetime__gt = datetime.utcnow())
			&
			Q(start_datime__lit = datetime.utcnow() + datetime.timeDelta(weeks=1))
		)
		return requests

	# Get's users availability in terms of their own timezone
	def availability_tz(self):
		returnArray = []
		for available_slot in self.availability:
			newSlot = available_slot
			newSlot['start_time'] += self.timezone * 2
			newSlot['end_time'] += self.timezone * 2
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
			returnArray.append(newSlot)
		return returnArray

	# Gets next 7 days of availability in UTC datetime objects
	def availability_this_week(self):
		returnArray = []
		for available_slot in self.availability:
			# Get a UTC object for the next Monday/Tuesday/etc...
			days_diff = available_slot['day']-today.weekday()
			available_utc_day = today + datetime.timedelta(days=days_diff, weeks=1)
			available_utc_day_midnight = datetime.datetime(
				year = available_utc_day.year,
				month = available_utc_day.month,
				day = available_utc_day.day
			)
			# Get a UTC datetime object with the correct time as well
			available_utc_start = (available_utc_day_midnight 
				+ datetime.timeDelta(
					minutes=(available_slot['start_time']*30
				))
			)
			returnArray.append(available_utc_start)
		return returnArray

	def add_property(self, property_type, property_data, affinity):
		# Check if property exists
		if property_type == 'work':
			property = UserProperty.objects(fb_id=property_data['employer']['id'])
		elif property_type == 'school':
			property = UserProperty.objects(fb_id=property_data['school']['id'])
		else:
			property = UserProperty.objects(fb_id=property_data['id'])
		if not property:
			# property doesn't exist... make it
			property = UserProperty(
				property_type = property_type
			)
			if property_type == 'work':
				property.name = property_data['employer']['name']
				property.fb_id = property_data['employer']['id']
				extra_fb_info = get_data_from_url('https://graph.facebook.com/'+str(property.fb_id),str(self.fb_access_token))
				property.thumburl = extra_fb_info['picture']
				property.website = extra_fb_info['website'] if extra_fb_info.get('website') else ''
				if property_data.get('location'):
					self.add_property('location', property_data['location'], 200)
			elif property_type == 'school':
				property.name = property_data['school']['name']
				property.fb_id = property_data['school']['id']
				property.school_type = property_data['type'] if property_data.get('type') else ''
				extra_fb_info = get_data_from_url('https://graph.facebook.com/'+str(property.fb_id),str(self.fb_access_token))
				property.thumburl = extra_fb_info['picture']
				if property_data.get('concentration'):
					for i in range(len(property_data['concentration'])):
						self.add_property('school_concentration', property_data['concentration'][i], 200)
			elif property_type == 'location':
				property.fb_id = property_data['id']
				property.name = property_data['name']
				extra_fb_info = get_data_from_url('https://graph.facebook.com/'+str(property.fb_id),str(self.fb_access_token))
				property.thumburl = extra_fb_info['picture']
				property.latlong = [extra_fb_info['location']['latitude'], extra_fb_info['location']['longitude']]
			else:
				property.fb_id = property_data['id']
				property.name = property_data['name']
			property.save()
		else:
			property = property.first()
		# Draw the link between the user and property
		propertyLink = UserPropertyLink.objects(user=self, user_property_id=property.id)
		if not propertyLink:
			propertyLink = UserPropertyLink(
				user = self,
				user_property_id = property.id,
				property_type = property_type,
				affinity = affinity
			)
			if property_type == 'work':
				if property_data.get('position') and property_data.get('position').get('name'):
					propertyLink.position = property_data['position']['name']
				else:
					propertyLink.position = ''
				propertyLink.description = property_data['description'] if property_data.get('description') else ''
				propertyLink.start_date = property_data['start_date'] if property_data.get('start_date') else ''
				propertyLink.end_date = property_data['end_date'] if property_data.get('end_date') else ''
			if property_type == 'school' and property_data.get('concentration'):
				concentration_string = ''
				for i in range(len(property_data['concentration'])):
					concentration_string += property_data['concentration'][i]['name'] + ', '
				concentration_string = concentration_string[:-2]
				propertyLink.position = concentration_string
		else:
			propertyLink = propertyLink[0]
			propertyLink.affinity = propertyLink.affinity + (affinity/10)
		propertyLink.save()


class Chat(Document):

	user_from = ReferenceField('User', required=True)
	user_to = ReferenceField('User', required=True)

	start_datetime = DateTimeField(required=True)
	end_datetime = DateTimeField(required=True)

	tok_session_id = IntField(required=True)

	user_from_in_chat = BooleanField(default=False)
	user_to_in_chat = BooleanField(default=False)

	user_to_join_chat_time = DateTimeField()
	user_from_join_chat_time = DateTimeField()

	def init_opentok(self):
		opentok_sdk = OpenTokSDK.OpenTokSDK(tok_api, tok_secret, staging=True)
		session = opentok_sdk.create_session('127.0.0.1')
		self.tok_session_id = session.session_id
		self.save()

	def gen_opentok_token(self):
		self.init_opentok()
		connectionMetadata = 'username=Bill' + '' + ', userLevel=4' # todo: username
		token = opentok_sdk.generate_token(self.tok_session_id, OpenTokSDK.RoleConstants.PUBLISHER, None, connectionMetadata)
		return token
