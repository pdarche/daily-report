from settings import *

# service wrapper imports 
import fitbit

# stdlib imports 
import json
from datetime import date

#template imports
from jinja2 import Template

# email imports 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def add_fitibt():
	f = fitbit.FitBit()
	token = 'oauth_token_secret=%s&oauth_token=%s' % (FITBIT_ACCESS_SECRET, FITBIT_ACCESS_KEY)
	today = date.today().strftime('%Y-%m-%d')
	resource_url = '/1/user/-/activities/date/%s.json' % today
	response = f.ApiCall(token, apiCall=resource_url)
	response_dict = json.loads(response)
	steps = response_dict['summary']['steps']


def send_mail(templates):
	EMAIL_TO = "pdarche@gmail.com"
	EMAIL_FROM = "pdarche@gmail.com"
	EMAIL_SUBJECT = "Test Fitbit"

	msg = MIMEMultipart('alternative')
	msg['Subject'] = "Test Fitbit"
	msg['From'] = EMAIL_FROM
	msg['To'] = EMAIL_TO

	text = "Hi!\nHow are you?\nHere is the link you wanted:\nhttp://www.python.org"
	html = """\
	<html>
	  <head></head>
	  <body>
	  	<div style="position:relative; margin: 0px auto; padding: 20px; width:800px; border: 1px solid #333; border-radius: 10px;">
	       How are you?<br>
	       You've taken %s today
	    </div>
	  </body>
	</html>
	""" % 1000000000000000

	part1 = MIMEText(text, 'plain')
	part2 = MIMEText(html, 'html')	

	msg.attach(part1)
	msg.attach(part2)

	mail = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
	mail.starttls()
	mail.login(SMTP_USERNAME, SMTP_PASSWORD)
	mail.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
	mail.quit()

send_mail('pizza')



