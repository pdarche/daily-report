#!/usr/bin/env python
from settings import *

# service wrapper imports 
import fitbit
import foursquare
import flickr_api

# stdlib imports 
import json
from datetime import date
import datetime
import time
import sys

#template imports
from jinja2 import Template
from jinja2 import FileSystemLoader
from jinja2.environment import Environment

# email imports 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class ReportGenerator():
	"""
		A class for generating daily (weekly, monthly, yearly) 
		email reports of self-tracking data.   
	"""

	def __init__(self, name, options):
		self.services = { 
			"name" : name,
			"date" : date.today().strftime('%A, %B %d'),
			"fitbit" : None,
			"withings" : None,
			"open_paths" : None,
			"foursquare" : None,
			"flickr" : None,
			"github" : None
		}

		self.service_data = {
			"fitbit" : self.add_fitbit,
			"withings" : self.add_withings,
			"open_paths" : None,
			"foursquare" : self.add_foursquare,
			"flickr" : self.add_flickr,
			"github" : self.add_github
		}
		# if service is in services.keys()
		# fetch and set that services data
		for service in options:
			if service in self.services:
				self.services[service] = self.service_data[service]()

		# self.services = dict(self.services.items() + {'name' : self.name}.items())
		self.send_mail()

	def add_fitbit(self):
		f = fitbit.FitBit()
		token = 'oauth_token_secret=%s&oauth_token=%s' % (FITBIT_ACCESS_SECRET, FITBIT_ACCESS_KEY)
		today = date.today().strftime('%Y-%m-%d')
		resource_url = '/1/user/-/activities/date/%s.json' % today
		response = f.ApiCall(token, apiCall=resource_url)
		response_dict = json.loads(response)
		fitbit_data = {
			"steps" : response_dict["summary"]["steps"],
			"steps_goal" : response_dict["goals"]["steps"],
			"distance" : response_dict["summary"]["distances"][0]["distance"],
			"distance_goal" : response_dict["goals"]["distance"],
			"cals_out" : response_dict["summary"]["caloriesOut"],
			"cals_out_goal" : response_dict["goals"]["caloriesOut"],
			"floors" : response_dict["summary"]["floors"],
			"floors_goal" : response_dict["goals"]["floors"]
		}		
		return fitbit_data

	def add_withings(self):
		# stuff to add here
		pass

	def add_foursquare(self):
		client = foursquare.Foursquare(client_id=FOURSQUARE_CLIENT_ID, client_secret=FOURSQUARE_CLIENT_SECRET, redirect_uri='http://127.0.0.1:8000')
		client.set_access_token(FOURSQUARE_ACCESS_TOKEN)
		today_string = date.today().strftime("%m/%d/%Y")
		today = int(time.mktime(datetime.datetime.strptime(today_string, "%m/%d/%Y").timetuple()))
		checkins = client.users.checkins(params={"afterTimestamp": today})["checkins"]["items"]
		return { "checkins":checkins }

		# TODO: figure out how to embed images
		# for checkin in checkins:
		# 	lat = checkin["venue"]["location"]["lat"]
		# 	lnf = checkin["venue"]["location"]["lng"]
		# 	name = checkin["venue"]["name"]

	def add_flickr(self):
		today_string = date.today().strftime("%m/%d/%Y")
		today = int(time.mktime(datetime.datetime.strptime(today_string, "%m/%d/%Y").timetuple()))		
		flickr_api.set_keys(api_key = FLICKR_API_KEY, api_secret = FLICKR_API_SECRET)
		a = flickr_api.auth.AuthHandler.load('/Users/pdarche/Desktop/daily-report/flickr_auth')
		flickr_api.set_auth_handler(a)
		user = flickr_api.test.login()
		meals = user.getPhotos(min_taken_date=today)
		return {"meals" : meals}

	def add_github(self):
		pass

	def send_mail(self):
		EMAIL_TO = "pdarche@gmail.com"
		EMAIL_FROM = "pdarche@gmail.com"
		EMAIL_SUBJECT = "Daily Report for %s" % date.today().strftime('%A, %B %d')

		msg = MIMEMultipart('alternative')
		msg['Subject'] = EMAIL_SUBJECT
		msg['From'] = EMAIL_FROM
		msg['To'] = EMAIL_TO

		text = "Hi!\nHow are you?\nHere is the link you wanted:\nhttp://www.python.org"
		html = self.render_templates()

		part1 = MIMEText(text, 'plain')
		part2 = MIMEText(html, 'html')	

		msg.attach(part1)
		msg.attach(part2)

		mail = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
		mail.starttls()
		mail.login(SMTP_USERNAME, SMTP_PASSWORD)
		mail.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
		mail.quit()

	def render_templates(self):
		env = Environment()
		env.loader = FileSystemLoader('/Users/pdarche/Desktop/daily-report/templates')
		tmpl = env.get_template('base.html')

		return tmpl.render(self.services)

report = ReportGenerator('Peter Darche', sys.argv[1:])



