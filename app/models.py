from django.db import models
from mongoengine import *
from datetime import datetime

import OpenTokSDK
tok_api = '14712672'
tok_secret = '3da704cbbda26bb38e50d430d0fecfd7ffc0269f'

# Connect to the DB
connect('air_test')

# UserLinkProperty
#   A specific common trait among users.
class UserLinkProperty(Document):

	name = StringField(required=True)
	latlong = GeoPointField()
	thumburl = StringField()

class UserAvailability(EmbeddedDocument):

	# Day: 0 = Sunday, 1 = Monday, ..., 6 = Saturday
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

class User(Document):

	def __unicode__(self):
		return self.getFullName()

	first_name = StringField(required=True)
	last_name = StringField(required=True)
	email = StringField(required=True)
	timezone = IntField(required=True)

	fb_id = IntField(required=True)
	is_admin = BooleanField(required=True, default=False)

	created_at = DateTimeField(required=True, default=datetime.utcnow())
	edited_at = DateTimeField(required=True, default=datetime.utcnow())

	workplace_ids = ListField(ObjectIdField())
	school_ids = ListField(ObjectIdField())
	location_ids = ListField(ObjectIdField())

	gender = StringField()
	bio = StringField()
	picture_url = StringField()

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
	
	def getFullName(self):
		return self.first_name + ' ' + self.last_name

	def workplaces(self):
		return UserLinkProperty.objects(id__in=self.workplace_ids)

	def schools(self):
		return UserLinkProperty.objects(id__in=self.school_ids)

	def locations(self):
		return UserLinkProperty.objects(id__in=self.location_ids)

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
