import os
import uuid
import json
import logging
import requests

from datetime import datetime
from flask import Flask, request

class DirectLineEngine():
	
	
	def __init__(self, token_endpoint):
		self.token_endpoint = token_endpoint
		self.current_token = None
		self.refresh_endpoint = "https://directline.botframework.com/v3/directline/tokens/refresh"
		self.conversations_endpoint = "https://directline.botframework.com/v3/directline/conversations"
									   
		
		
	def get_token(self):
		base_url = self.token_endpoint
		try: 
			token_response = requests.get(base_url)
			if token_response.status_code == 200:
				return token_response.json()['token'], token_response.json()['conversationId']
			else:
				logging.warning(token_response.status_code)
				logging.warning(token_response.text)
				return None, None
		except:
			return None, None
			
	def create_conversation(self, token):
		headers = {'Authorization': f'Bearer {token}'}
		try:
			r = requests.post(self.conversations_endpoint, headers=headers)
			if r.status_code == 201:
				return r
			else:
				logging.warning(r.status_code)
				logging.warning(r.text)
				return False
		except:
			return False
			
		
	def refresh_token(self, token):
		headers = {'Authorization': f'Bearer {token}'}
		try:
			r = requests.post(self.refresh_endpoint, headers=headers)
			if r.status_code == 200:
				return r
			else:
				logging.warning(r.status_code)
				logging.warning(r.text)
				return False
		except:
			return False
			
	def send_activity(self, token, conversationId, text):
		url = f"{self.conversations_endpoint}/{conversationId}/activities"
		headers = {
			'Authorization': f'Bearer {token}',
			'Content-Type':'application/json'
		}
		body = {
		  "locale": "en-EN",
		  "type": "message",
		  "from": {
			"id": "user1"
		  },
		  "text": text
		}
		try:
			r = requests.post(url, headers=headers, json=body)
			logging.warning(r.text)
			if r.status_code == 200:
				return r.json()["id"]
			else:
				logging.warning(r)
				logging.warning(r.text)
				return False
		except Exception as e:
			logging.warning(e)
			return False
		
			
	def get_activity(self, token, conversationId, watermark=None):
		url = f"{self.conversations_endpoint}/{conversationId}/activities"
		headers = {
			'Authorization': f'Bearer {token}'
		}
		params = {}
		if watermark:
			params['watermark'] = watermark
		
		try:
			r = requests.get(url, headers=headers, params=params)
			if r.status_code == 200:
				return r.json()
			else :
				logging.warning(r)
				logging.warning(r.text)
				return False
		except Exception as e:
			logging.warning(e)
			return False
			
			
		
		
		