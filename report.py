#!/usr/bin/env python
from settings import *
import requests

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

		self.send_mail()

	def add_fitbit(self):
		f = fitbit.FitBit()
		token = 'oauth_token_secret=%s&oauth_token=%s' % (FITBIT_ACCESS_SECRET, FITBIT_ACCESS_KEY)
		today = date.today().strftime('%Y-%m-%d')
		activities_url = '/1/user/-/activities/date/%s.json' % today
		foods_url = '/1/user/-/foods/log/date/%s.json' % today
		sleep_url = '/1/user/-/sleep/date/%s.json' % today
		foods = self._fetch_fitibit(f, token, foods_url)
		activities = self._fetch_fitibit(f, token, activities_url)
		sleep = self._fetch_fitibit(f, token, sleep_url)

		return {
			"logged_foods": self._prep_foods(foods['foods']),
			"activities": self._pre_activities(activities),
			"sleep": self._prep_sleep(sleep['sleep'])
		}

	def _fetch_fitibit(self, f, token, url):
		response = f.ApiCall(token, apiCall=url)
		return json.loads(response)

	def _pre_activities(self, activities):
		return {
			"steps" : activities["summary"]["steps"],
			"steps_goal" : activities["goals"]["steps"],
			"distance" : activities["summary"]["distances"][0]["distance"],
			"distance_goal" : activities["goals"]["distance"],
			"cals_out" : activities["summary"]["caloriesOut"],
			"cals_out_goal" : activities["goals"]["caloriesOut"],
			"floors" : activities["summary"]["floors"],
			"floors_goal" : activities["goals"]["floors"]
		}

	def _prep_foods(self, foods):
		logged_foods = map(lambda f: f['loggedFood']['name'], foods)
		nutritionalValues = map(lambda f: f['nutritionalValues'], foods)
		return {
			"foods" : logged_foods,
			"totals" : {
				"carbs": sum(f['carbs'] for f in nutritionalValues),
				"fiber": sum(f['fiber'] for f in nutritionalValues),
				"sodium": sum(f['sodium'] for f in nutritionalValues),
				"calories": sum(f['calories'] for f in nutritionalValues),
				"fat": sum(f['fat'] for f in nutritionalValues),
				"protein": sum(f['protein'] for f in nutritionalValues)
			}
		}

	def _prep_sleep(self, sleep):
		return {
			"mins_to_sleep": sleep[0]['minutesToFallAsleep'],
			"awakenings_count": sleep[0]['awakeningsCount'],
			"minutes_awake": sleep[0]['minutesAwake'],
			"hrs_sleep": round(float(sleep[0]['minutesAsleep'])/60,2),
			"efficiency": sleep[0]['efficiency'],
			"bed_time": sleep[0]['startTime']
		}

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

		text = "Some neat text"
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

# report = ReportGenerator('Piotr Darchovskavitch', sys.argv[1:])
report = ReportGenerator('Piotr Darchovskavitch', ['fitbit', 'foursquare', 'flickr'])
