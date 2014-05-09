from django.db import models
from mongoengine import *
import datetime
from mongoengine.django.auth import User as MongoUser
from airety.utils import get_data_from_url

import OpenTokSDK
tok_api = '14712672'
tok_secret = '3da704cbbda26bb38e50d430d0fecfd7ffc0269f'


# UserLinkProperty
#   A specific common trait among users.
class UserProperty(Document, EmbeddedDocument):

	def __unicode__(self):
		return str(self.property_type) + ': ' + self.name

	name = StringField(required=True)
	fb_id = IntField()
	position = StringField() # Used when embedded
	property_type = StringField(required=True)
	latlong = GeoPointField()
	thumburl = StringField()

class UserPropertyLink(Document):

	def __unicode__(self):
		return str(self.affinity) + ': ' + self.property_type

	user = ReferenceField('User', required=True)
	user_property_id = ObjectIdField(required=True)
	property_type = StringField(required=True)
	position = StringField()
	description = StringField()
	start_time = StringField()
	end_time = StringField()
	affinity = IntField(required=True, default=200)
	affinity_actions = IntField(default=0)
	highlighted = BooleanField(default=False)

class UserAvailability(EmbeddedDocument):

	# Day: 0 = Monday, ..., 6 = Sunday 
	day = IntField(required=True)

	# Times: 0 = 12AM, 1 = 12:30AM, 2 = 1AM, ..., 47 = 11:30PM
	start_time = IntField(required=True)
	end_time = IntField(required=True)

class ChatRequest(Document):

	request_from = ReferenceField('User', required=True)
	request_to = ReferenceField('User', required=True)
	
	start_datetime = DateTimeField(required=True)
	end_datetime = DateTimeField(required=True)

	request_to_confirm = BooleanField(required=True, default=False)
	request_form_confirm = BooleanField(required=True, default=False)
	
	message = StringField(max_length=300)

# Used in objects to store some basic user information
class BasicUser(EmbeddedDocument):

	username = StringField(required=True)
	name = StringField(required=True)
	first_name = StringField(required=True)
	last_name = StringField(required=True)
	email = StringField(required=True)
	fb_id = IntField(required=True)
	picture_url = StringField()
	picture_width = IntField()
	picture_height = IntField()
	thumb_url = StringField()

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

	created_at = DateTimeField(required=True, default=datetime.datetime.utcnow())
	edited_at = DateTimeField(required=True, default=datetime.datetime.utcnow())

	gender = StringField()
	bio = StringField()
	picture_url = StringField()
	picture_width = IntField()
	picture_height = IntField()
	thumb_url = StringField()

	has_availability = BooleanField(default=False)
	availability = ListField(EmbeddedDocumentField(UserAvailability))
	featured_properties = ListField(EmbeddedDocumentField(UserProperty))
	requests_out = ListField(ReferenceField('ChatRequest'))
	requests_in = ListField(ReferenceField('ChatRequest'))

	chats = ListField(ReferenceField('Chat'))

	# Track
	sign_in_count = IntField(default=0)
	last_sign_in_at = DateTimeField(default=datetime.datetime.utcnow())
	schedule_viewed_count = IntField(default=0)
	chat_out_request_count = IntField(default=0)
	chat_out_request_accepted_count = IntField(default=0)
	chat_in_request_count = IntField(default=0)
	chat_in_request_accepted_count = IntField(default=0)

	def set_default_featured_properties(self):
		workLink = UserPropertyLink.objects(
			user=self,
			property_type='work'
		).order_by('-affinity').limit(1)
		schoolLink = UserPropertyLink.objects(
			user=self,
			property_type='school'
		).order_by('-affinity').limit(1)
		locationLink = UserPropertyLink.objects(
			user=self,
			property_type='location'
		).order_by('-affinity').limit(1)
		featuredProp = []
		if len(workLink) > 0:
			up = UserProperty.objects(id=workLink[0].user_property_id)[0]
			up.position = workLink[0].position
			featuredProp.append(up)
		if len(schoolLink) > 0:
			up = UserProperty.objects(id=schoolLink[0].user_property_id)[0]
			up.position = schoolLink[0].position
			featuredProp.append(up)
		if len(locationLink) > 0:
			up = UserProperty.objects(id=locationLink[0].user_property_id)[0]
			up.position = locationLink[0].position
			featuredProp.append(up)
		self.featured_properties = featuredProp
		self.save()
		return

	def getFullName(self):
		return self.first_name + ' ' + self.last_name

	def get_basic_user_object(self):
		return BasicUser(
			username = self.username,
			name = self.name,
			first_name = self.first_name,
			last_name = self.last_name,
			email = self.email,
			fb_id = self.fb_id,
			picture_url = self.picture_url,
			picture_width = self.picture_width,
			picture_height = self.picture_height,
			thumb_url = self.thumb_url
		)

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
			Q(start_datetime__gt = datetime.datetime.utcnow())
			&
			Q(start_datetime__lt = datetime.datetime.utcnow() + datetime.timedelta(weeks=1))
		)
		return chats

	def incoming_requests_this_week(self):
		requests = ChatRequest.objects(
			Q(request_to = self)
			&
			Q(start_datetime__gt = datetime.datetime.utcnow())
			&
			Q(start_datetime__lt = datetime.datetime.utcnow() + datetime.timedelta(weeks=1))
		)
		return requests

	def outgoing_requests_this_week(self):
		requests = ChatRequest.objects(
			Q(request_from = self)
			&
			Q(start_datetime__gt = datetime.datetime.utcnow())
			&
			Q(start_datetime__lt = datetime.datetime.utcnow() + datetime.timedelta(weeks=1))
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
		today = datetime.datetime.utcnow()
		for available_slot in self.availability:
			# Get a UTC object for the next Monday/Tuesday/etc...
			days_diff = available_slot['day']-today.weekday()
			available_utc_day = today + datetime.timedelta(days=days_diff)
			available_utc_day_midnight = datetime.datetime(
				year = available_utc_day.year,
				month = available_utc_day.month,
				day = available_utc_day.day
			)
			# Get a UTC datetime object with the correct time as well
			available_utc_start = (available_utc_day_midnight 
				+ datetime.timedelta(
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
		connectionMetadata = 'username=' + self.user_from.username + ', userLevel=4'
		token = opentok_sdk.generate_token(self.tok_session_id, OpenTokSDK.RoleConstants.PUBLISHER, None, connectionMetadata)
		return token
