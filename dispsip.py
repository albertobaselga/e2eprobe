import datetime

from base64 import b64encode
import json
import requests
import urllib
import ConfigParser
import ast
import pjsua as pj
import logging
import random
from time import sleep
import user

#from user import user_call_handler


## Initializing library

## Defining DispSIP Class
class dispsip:

	_user=None
	metrics={}

	def __init__(self,user, log_level=6):
		## Load config file
		self._config = ConfigParser.ConfigParser()
		self._config.read('./config.cfg')

		## Initialize logger
		dispsip._user=user
		self._user=user
		self._user_code=user.user_code
		self.logger = logging.getLogger(self._user_code+'.dispsip')
		self.logger.info('Initializing SIP device for user: %s',self._user_code)

		## Initializing SIP device
		if not pj.Lib.instance():
			lib = pj.Lib()
		else:
			lib = pj.Lib.instance()

		my_ua_cfg = pj.UAConfig()
               	my_media_cfg = pj.MediaConfig()

                try:
			self.logger.debug('Initializing PJSUA library')
                        lib.init(log_cfg=pj.LogConfig(level=log_level, callback=log_cb), ua_cfg=my_ua_cfg, media_cfg=my_media_cfg)
			self.logger.debug('Setting null sound device in PJSUA library')
                        lib.set_null_snd_dev()
			
                except pj.Error, e:
                        self.logger.error('Lib Initialization error: %s', e)

		try:
            		self.logger.debug('Starting PJSUA library.')
			lib.start(with_thread=True)
		except pj.Error, e:
                        self.logger.error('Error starting pjsua library:i %s', e)

	def disconnect(self):
		try:
			self.logger.info('Disconnecting')
           		pj.Lib.instance().destroy()
		except pj.Error, e:
			self.logger.error('Error disconnecting SIP device: %s',e)

	
	def connect(self):

		self.logger.info('Connecting SIP device.')
		lib = pj.Lib.instance()

		self.metrics['connect']={}
		self.metrics['handled_sms']=[]
		self.metrics['handled_call']=[]
		self.metrics['send_sms']=[]
                self.metrics['dial_call']=[]

			
		if not self._login():
			self.logger.error('Login error')
			return False
		if not self._authenticate():
			self.logger.error('Authentication error')
			return False

		## Transport / Listener
                try:
			self.logger.debug('Creating transport...')
                        tr = lib.create_transport(pj.TransportType.TLS, pj.TransportConfig(random.randint(1024, 64 * 1024),'0.0.0.0'))
			self.logger.debug('Transport created. Type:%s, description:%s, is_reliable:%s, is_secure:%s, is_datagram:%s, host:%s, port:%s, ref_cnt:%s',tr.info().type,tr.info().description, tr.info().is_reliable,tr.info().is_secure, tr.info().is_datagram, tr.info().host, tr.info().port, tr.info().ref_cnt)
                except pj.Error, e:
                        self.logger.error('Error creating transport:', e)

		## SIP Account
		self.logger.debug('Creating sip account')
                acc_cfg = pj.AccountConfig()
                acc_cfg.id = '"{0}" <sip:{1}@{2}>'.format(self._sip_name, self._sip_username, self._sip_domain)
                acc_cfg.reg_uri = "sip:"+self._sip_domain
                acc_cfg.proxy.append(self._sip_proxy)
                acc_cfg.auth_cred = [ dispsip.AuthCred("*", self._msisdn, self._sip_pass) ]

		try:
                        acc_cb = dispsip.MyAccountCallback()
			self.logger.debug('Account Data: %s',acc_cfg.__dict__)
                        self._acc = lib.create_account(acc_cfg, set_default=True, cb=acc_cb)
			sleep(3.0)

                except pj.Error, e:
                        self.logger.error('Error registering account:', e)

		self.logger.info('Device successfully registered.')

	def _authenticate(self):
		user_agent = self._config.get('SIP_CFG','user_agent')
		url = self._config.get('SIP_CFG','url_auth')

                _auth= b64encode('%s:%s' % (self._sip_user_id,self._sip_pass))
                headers = {'Authorization': 'Basic ' + _auth,
                        'User-Agent': user_agent,
                        'Content-Type': "application/json;charset=UTF-8"}

		self.logger.info('Authenticating user')
		m={}
		m['auth_start']= str(datetime.datetime.now())
		response = requests.post(url, None, headers=headers)
		m['auth_finish']= str(datetime.datetime.now())
		m['auth_status_code']=response.status_code
		self.metrics['connect']['authentication']=m
		if response.status_code==200:
			params = json.loads(response.content)
			self.logger.debug('Authentication server answer: %s',params)
			self._validToken = str(params['access_token'])
			return True
		else:
			self.logger.error('Error authenticating user. HTTP response code: %s',response.status_code)
			return False

        def _login(self):
		self._msisdn = ast.literal_eval(self._config.get('SIP_CREDENTIALS',self._user_code))['msisdn']
		password = ast.literal_eval(self._config.get('SIP_CREDENTIALS',self._user_code))['password']
		url = self._config.get('SIP_CFG','url_login')
		user_agent = self._config.get('SIP_CFG','user_agent')

                _auth = b64encode('%s:%s' % (self._msisdn, password))
                headers = {'Authorization': 'Basic ' + _auth,
                        'User-Agent': user_agent,
                        'Content-Type': "application/json;charset=UTF-8"}

		self.logger.info('Loging user')
		m={}
		m['login_start'] = str(datetime.datetime.now())

                response = requests.post(url, None, headers=headers)
		m['login_finish'] = str(datetime.datetime.now())
		m['login_status_code'] = response.status_code
		self.metrics['connect']['login']=m
		if response.status_code==200:
			params = json.loads(response.content)
			self.logger.debug('Login server answer: %s',params)
	
                	self._sip_pass = str(params['user']['password'])
                	self._sip_name = str(params['user']['screen_name'])
                	self._sip_user_id = str(params['user']['user_id'])
                	self._sip_username = str(params['config']['sip']['username'])
                	self._sip_domain = str(params['config']['sip']['domain'])
                	self._sip_proxy = str(params['config']['sip']['proxy'])
                	self._sip_pstnDomain = str(params['config']['sip']['pstn_domain'])
			return True
		else:
			self.logger.error('Error loging user. HTTP response code: %s',response.status_code)
			return False

	def send_sms(self, destination, content, content_type='text/plain;charset=utf-8'):
                uri = str('sip:'+str(destination)+'@'+self._sip_pstnDomain)
                to = str('sip:00'+str(destination)+'@'+self._sip_pstnDomain)
		
		headers = [('Comm-Notifications', 'delivered, displayed'),
                  	('Comm-Logging', 'on'),
                   	('Comm-Type', 'text')]
		try:
			self.logger.info('Adding buddy [%s] to user [%s]',uri,self._user_code)
                	buddy = self._acc.add_buddy(uri, cb=dispsip.BuddyCallback())
			#buddy2 = self._acc.add_buddy(uri, request_uri=to, cb=BuddyCallback())
			#buddy.subscribe()	
		except pj.Error, e:
			self.logger.error('Error adding buddy %s. Error: %s',uri, e)

		self.logger.info('Sending IM to buddy [%s] from user[%s]',uri,self._user_code)
                buddy.send_pager(content, content_type=content_type, hdr_list=headers)


        def call(self, destination):
                uri = 'sip:'+str(destination)+'@'+str(self._sip_pstnDomain)
		try:
			self.logger.info('Making call to URI: %s',uri)
                	self._acc.make_call(uri, cb=dispsip.MyCallCallback())
		except pj.Error, e:
			self.logger.error('Error making call to %s. Error: %s',uri, e)

        def get_profile(self):
                user_agent = self._config.get('SIP_CFG','user_agent')
		url = self._config.get('SIP_CFG','url_profile')

		self.logger.info('Getting Profile')
                headers = {'Authorization': 'Bearer ' + self._validToken,
                        'User-Agent': user_agent,
                        'Content-Type': "application/json;charset=UTF-8"}

                response = requests.get(url, headers=headers)
		self.logger.info('Profile: %s',json.loads(response.content))
                return json.loads(response.content)


        def get_history(self, history_version=0):
                user_agent = self._config.get('SIP_CFG','user_agent')
                url = self._config.get('SIP_CFG','url_history')
 
		self.logger.info('Getting history')
                headers = {'Authorization': 'Bearer ' + self._validToken,
                        'User-Agent': user_agent,
                        'Content-Type': "application/json;charset=UTF-8"}

                params = urllib.urlencode({'from_version': history_version,
                        'page_size': 100,
                        'page_number': 1})

		url = url+params
                response = requests.get(url, headers=headers)
		self.logger.info('History: %s',json.loads(response.content))
                return json.loads(response.content)



	## Aux functions

	class MyCallCallback(pj.CallCallback):
    		""" Callback to receive events from Call """

		dtmf=''
		m={}

    		def __init__(self, call=None):
			self.logger = logging.getLogger('device.'+dispsip._user.user_code+'.dispsip')
        		pj.CallCallback.__init__(self, call)
			self.dtmf=''
			self.m={}
			self.m['call_start']=str(datetime.datetime.now())
			self.m['status_changes']=[]
			dispsip._user.user_call_handler('sip')
			

		def on_dtmf_digit(self, digits):
			self.logger.info('DTMF Tones received: %s',digits)
			self.dtmf=self.dtmf+str(digits)

    		def on_state(self):
        		""" Notification when call state has changed """
			me={}
			me['date_change']=str(datetime.datetime.now())
			me['status']=self.call.info().state_text
			me['last_code']=self.call.info().last_code
			me['last_reason']=self.call.info().last_reason
			me['call_time']=self.call.info().call_time
			me['total_time']=self.call.info().total_time
			self.m['status_changes'].append(me)
			self.logger.info('Call status has changed. contact:%s, remote_uri:%s, remote_contact:%s, sip_call_id:%s, state_text:%s, last_code:%s, last_reason:%s, call_time:%s, total_time:%s', self.call.info().contact, self.call.info().remote_uri, self.call.info().remote_contact, self.call.info().sip_call_id, self.call.info().state_text, self.call.info().last_code, self.call.info().last_reason, self.call.info().call_time, self.call.info().total_time)
			if self.call.info().state == pj.CallState.DISCONNECTED:
				self.m['destination']=self.call.info().contact
				self.m['remote_uri']=self.call.info().remote_uri
				self.m['remote_contact']=self.call.info().remote_contact
				self.m['sip_call_id']=self.call.info().sip_call_id
				self.m['call_finished']=str(datetime.datetime.now())
				self.m['dtmf_received']=self.dtmf
				dispsip.metrics['handled_call'].append(self.m)
            			self.logger.info('This call [%s] has been disconnected',self.call.info().sip_call_id)


    		def on_media_state(self):
        		if self.call.info().media_state == pj.MediaState.ACTIVE:
            			# Connect the call to sound device
            			call_slot = self.call.info().conf_slot
            			pj.Lib.instance().conf_connect(call_slot, 0)
            			pj.Lib.instance().conf_connect(0, call_slot)
            			self.logger.info('Media is now active')
        		else:
            			self.logger.info('Media is inactive')


	class AuthCred(object):
    		def __init__(self, realm="*", username="", passwd="", scheme="Digest", passwd_type=0):
			#self.logger = logging.getLogger('device.user.dispsip')
			self.logger = logging.getLogger('device.'+dispsip._user.user_code+'.dispsip')
        		self.scheme = scheme
        		self.realm = realm
        		self.username = username
        		self.passwd_type = passwd_type
        		self.passwd = passwd

	class BuddyCallback(pj.BuddyCallback):
    		def __init__(self, buddy=None):
        		pj.BuddyCallback.__init__(self, buddy)
			#self.logger = logging.getLogger('device.user.dispsip')
			self.logger = logging.getLogger('device.'+dispsip._user.user_code+'.dispsip')
	
		def on_state(self):
			self.logger.info('Buddy state has changed: %s', self.buddy.info().sub_state)

    		def on_pager(self, mime_type, body):
        		self.logger.info('Incoming IM %s %s %s', self.buddy, mime_type, body)
			m={}
			m['sms_body']=body
			m['arrival_date']=str(datetime.datetime.now())
			m['originator']=self.buddy
			dispsip.metrics['handled_sms'].append(m)
			dispsip._user.user_sms_handler('sip')
			
    		def on_pager_status(self, body, im_id, code, reason):
        		self.logger.info('Delivery status of IM %s %s %s %s', self.buddy, im_id, code, reason)
        		#self.buddy.delete()



	class MyAccountCallback(pj.AccountCallback):
    		def __init__(self, account=None):
        		pj.AccountCallback.__init__(self, account)
			#self.logger = logging.getLogger('device.user.dispsip')
			self.logger = logging.getLogger('device.'+dispsip._user.user_code+'.dispsip')
	
    		def on_incoming_call(self, call):
			self.logger.info('New call incoming, contact:%s, remote_uri:%s, sip_call_id:%s, state_text:%s, last_code:%s, last_reason:%s, call_time:%s, total_time:%s', call.info().contact, call.info().remote_uri, call.info().sip_call_id, call.info().state_text, call.info().last_code, call.info().last_reason, call.info().call_time, call.info().total_time)
        		my_cb = dispsip.MyCallCallback()
        		call.set_callback(my_cb)
			#sleep(2)
			self.logger.info('Answering call %s', call.info().sip_call_id)
			call.answer()


    		def on_reg_state(self):
        		self.logger.info("Registration status has changed. status= %s ( %s )", self.account.info().reg_status, self.account.info().reg_reason)

		def on_pager(self, from_uri, contact, mime_type, body):
			self.logger.info('New IM received. from: %s, body: %s',from_uri,body)
			m={}
                        m['sms_body']=body
                        m['arrival_date']=str(datetime.datetime.now())
                        m['originator']=from_uri
                        dispsip.metrics['handled_sms'].append(m)

			dispsip._user.user_sms_handler('sip')

def log_cb(level, str, len):
	logger = logging.getLogger('device.pjsua')
	logger.debug(str.strip())

if __name__ == '__main__':
	
	#logging.basicConfig(level=logging.DEBUG)
	FORMAT = '%(asctime)-15s %(name)s %(levelname)s %(message)s'
	logging.basicConfig(level=logging.DEBUG,format=FORMAT)
	#logging.basicConfig(level=logging.INFO,format=FORMAT)

	user = user.user('user1')
	disp1 = dispsip(user)
	sleep (1)
	print "Created"
	disp1.connect()
	sleep(500)
	disp1.send_sms('34699697868','HOLA')
	sleep(5)
	disp1.send_sms('0034699697868','HOLA')
	sleep(5)
	disp1.send_sms('4434699697868','HOLA')
	sleep(5)
	disp1.send_sms('00447730520578','HOLA')
	sleep(5)
	disp1.send_sms('7730520578','HOLA')
	sleep(5)
	disp1.send_sms('07730520578','HOLA')
	#disp1.get_profile()
	#disp1.get_history()
	sleep(5)
	disp1.call('0034699697868')
	sleep(5)
	disp1.call('4434699697868')
	sleep(5)
	disp1.call('34699697868')
	sleep(500)
	disp1.disconnect()

	print "FIN"
