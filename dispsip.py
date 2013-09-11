##
## Class SIP device
##
import json
import requests
import urllib
from base64 import b64encode
from time import sleep
import sys
import random

#sys.path.append('./pjsua/')
import pjsua as pj
from pjsua import *



TU_BE_URL = "https://api.tugoapp.com"
USER_AGENT = "GConnect/1.0 (P; Apple; iPhone; iPhone OS; 5.1;)"
DEVICEID = "7e8049ad-f919-3290-858f-7f6b7ee8ae2c"

class dispsip:
	def __init__(self, msisdn, password):
		self._msisdn = msisdn
		self._pass = password
		self._user_id = None
		self._sip_pass = None
		self._validToken =None

		self._lib = pj.Lib()


	def _initializeAccount(self):
		try:
			acc_cfg = pj.AccountConfig()
			#acc_cfg.id = '"{0}" <sip:{1}@{2}>'.format(self._sip_name, self._sip_username, self._sip_domain)
			acc_cfg.id = "sip:447730520578@voip.gconnect.jajah.com"
			#acc_cfg.reg_uri = "sip:"+self._sip_domain
			acc_cfg.reg_uri = "sip:voip.gconnect.jajah.com"
			#acc_cfg.reg_uri = "sip:447730520578@voip.gconnect.jajah.com"
			#acc_cfg.user_agent = USER_AGENT
			#acc_cfg.proxy.append(self._sip_proxy)
			acc_cfg.proxy = [ "sip:voip.gconnect.jajah.com:443;transport=TLS" ]
			acc_cfg.auth_cred = [ AuthCred("*", self._sip_username, self._sip_pass) ]
			#acc_cfg.allow_contact_rewrite = 0
			
			acc_cb = MyAccountCallback()
			self._acc = self._lib.create_account(acc_cfg, set_default=True, cb=acc_cb)

		except pj.Error, err:
			print 'Error creating account:', err
		

	def _initializeTransport(self):
		try:    
                        self._udp = self._lib.create_transport(pj.TransportType.TLS, pj.TransportConfig(random.randint(1024, 64 * 1024),'0.0.0.0'))
                except pj.Error, e:
                        print "Error creating transport:", e

	def _initializeLib(self):
		try:
                        my_ua_cfg = pj.UAConfig()
                        #my_ua_cfg.user_agent = "E2E TuGO Probe"
			my_ua_cfg.user_agent = USER_AGENT			
			my_ua_cfg.max_calls = 5

                        my_media_cfg = pj.MediaConfig()
                        my_media_cfg.enable_ice = True
			#my_media_cfg.channel_count = 0

                        self._lib.init(ua_cfg=my_ua_cfg, media_cfg=my_media_cfg)
			self._lib.set_null_snd_dev()

                except pj.Error, err:
                        print 'Lib Initialization error:', err

	def get_profile(self):
		headers = {'Authorization': 'Bearer ' + self._validToken,
                	'User-Agent': USER_AGENT+"("+DEVICEID+")",
                   	'Content-Type': "application/json;charset=UTF-8"}

        	response = requests.get(TU_BE_URL + '/users/me', headers=headers)
        	return json.loads(response.content)


	def get_history(self, history_version=0):
		headers = {'Authorization': 'Bearer ' + self._validToken, 
			'User-Agent': USER_AGENT+"("+DEVICEID+")",
                   	'Content-Type': "application/json;charset=UTF-8"}

        	params = urllib.urlencode({'from_version': history_version,
                	'page_size': 100,
                        'page_number': 0})
        	response = requests.get(TU_BE_URL + '/users/me/history?' + params, headers=headers)
		return json.loads(response.content)

	def send_sms(self, destination, content, content_type='text/plain;charset=utf-8'):
		header = [('Comm-Notifications', 'delivered, displayed'),
			('Comm-ID','1234567890'),
               		('Comm-Logging', 'on'),
               		('Comm-Type', 'message')]
		#uri = "sip:"+str(destination)+"@"+self._sip_pstnDomain
		uri = "sip:0034699697868@o2uk.gconnect.jajah.com"
 		buddy = self._acc.add_buddy(uri, cb=BuddyCallback())
        	buddy.send_pager(content, content_type=content_type, hdr_list=header)

	def call(self, destination):
		header = [('Comm-Notifications', 'delivered, displayed'),
                        ('Comm-ID',DEVICEID),
                        #('Comm-ID','18916357-4f52-400f-99be-4c94cf0996bb'),
                        ('Comm-Logging', 'on'),
                        ('Content-Type', 'application/sdp'),
 			('Comm-Type', 'call')]

		#uri = "sip:"+str(destination)+"@"+self._sip_pstnDomain
		uri = "sip:0034699697868@o2uk.pstn.gconnect.jajah.com"
		self._acc.make_call(uri, hdr_list=header, cb=MyCallCallback())

	def connect(self):
		try:
			self._lib.start()
		except pj.Error, e:
			print "Error starting pjsua library:", e
		#login
		self._configLogin = self._login()
		self._sip_pass = self._configLogin['user']['password']
		self._sip_name = self._configLogin['user']['screen_name']
		self._sip_user_id = self._configLogin['user']['user_id']
		self._sip_username = self._configLogin['config']['sip']['username']
		self._sip_domain = self._configLogin['config']['sip']['domain']
		self._sip_proxy = self._configLogin['config']['sip']['proxy']
		self._sip_pstnDomain = self._configLogin['config']['sip']['pstn_domain']

		#Auth
		self._configAuth = self._authenticate() 
		self._validToken = self._configAuth['access_token']

		self._initializeLib()
		self._initializeTransport()
		self._initializeAccount()
		print 'Connected.'

	def _login(self):
		_auth = b64encode('%s:%s' % (self._msisdn, self._pass))
		headers = {'Authorization': 'Basic ' + _auth,
                	'User-Agent': USER_AGENT+"("+DEVICEID+")",
                	'Content-Type': "application/json;charset=UTF-8"}

        	response = requests.post(TU_BE_URL + '/users/login', None, headers=headers)
        	return json.loads(response.content)

	def _authenticate(self):
		_auth= b64encode('%s:%s' % (self._configLogin['user']['user_id'], self._configLogin['user']['password']))
        	headers = {'Authorization': 'Basic ' + _auth,
                   	'User-Agent': USER_AGENT+"("+DEVICEID+")",
                   	'Content-Type': "application/json;charset=UTF-8"}

        	response = requests.post(TU_BE_URL + '/users/me/authorization', None, headers=headers)
        	return json.loads(response.content)


	def disconnect(self):
		self._lib.destroy()
		self._lib = None

class AuthCred(object):
	"""Authentication credential for SIP or TURN account.
	Member documentation:
	
	scheme      -- authentication scheme (default is "Digest")
	realm       -- realm
	username    -- username
	passwd_type -- password encoding (zero for plain-text)
	passwd      -- the password
	"""

	def __init__(self, realm="*", username="", passwd="", scheme="Digest", passwd_type=0):
		self.scheme = scheme
		self.realm = realm
		self.username = username
		self.passwd_type = passwd_type
		self.passwd = passwd



class MyAccountCallback(pj.AccountCallback):
	def __init__(self, account=None):
		pj.AccountCallback.__init__(self, account)



	def on_incoming_call(self, call):
		my_cb = MyCallCallback()
		call.set_callback(my_cb)


	#def on_incoming_call(self, call):
		#call.hangup(501, "Sorry, not ready to accept calls yet")

	def on_reg_state(self):
		print "Registration status=", self.account.info().reg_status, \
			"(" + self.account.info().reg_reason + ")"


class MyCallCallback(pj.CallCallback):
	""" Callback to receive events from Call """

	def __init__(self, call=None):
		pj.CallCallback.__init__(self, call)

	def on_state(self):
		""" Notification when call state has changed """
		print ('on_state %s', self.call)
		print ("Call is %s", self.call.info().state_text)
		print ("last code %s", self.call.info().last_code)
		print ("(%s)", self.call.info().last_reason)

	def on_media_state(self):
		""" Notification when call's media state has changed. """
		print ('on_media_state %s', self.call)
		if self.call.info().media_state == pj.MediaState.ACTIVE:
			# Connect the call to sound device
			call_slot = self.call.info().conf_slot
			pj.Lib.instance().conf_connect(call_slot, 0)
			pj.Lib.instance().conf_connect(0, call_slot)

	def on_dtmf_digit(self, digits):
		print 'DTMF Digits %s' % digits


class BuddyCallback(pj.BuddyCallback):
	def __init__(self, buddy=None):
		pj.BuddyCallback.__init__(self, buddy)

	def on_pager(self, mime_type, body):
		#logger.info('on_pager %s %s %s', self.buddy, mime_type, body)
		print 'on_pager %s %s %s' % (self.buddy, mime_type, body)
		#self.listener.on_message('MESSAGE', self.buddy.info().uri, mime_type, body, [])

	def on_pager_status(self, body, im_id, code, reason):
		#logger.info('on_pager_status %s %s %s', code, self.buddy, body)
		print 'on_pager_status %s %s %s' % (code, self.buddy, body)
		self.buddy.delete()



if __name__ == '__main__':
	d = dispsip(447730520578,'alb15886')
	d.connect()
	sleep(3.0)
	#d.send_sms("0034699697868","HOLA")
	#print d.get_history()
	d.call('0034699697868')
	sleep(1.0)
	d.disconnect()
