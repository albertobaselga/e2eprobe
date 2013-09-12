from base64 import b64encode
import json
import requests
import ConfigParser
import ast
import pjsua as pj
import logging
import random
from time import sleep



## Initializing library
config = ConfigParser.ConfigParser()
config.read('./config.cfg')
logger = logging.getLogger('dispsip')

## Defining DispSIP Class
class dispsip:
	def __init__(self,user_code='user1', log_level=6):
		logger.info('Initializing SIP device for user: %s',user_code)
		self._user=user_code
		if not pj.Lib.instance():
			lib = pj.Lib()
			my_ua_cfg = pj.UAConfig()
                	my_media_cfg = pj.MediaConfig()

                	try:
				logger.debug('Initializing PJSUA library')
                        	lib.init(log_cfg=pj.LogConfig(level=log_level, callback=log_cb), ua_cfg=my_ua_cfg, media_cfg=my_media_cfg)
				logger.debug('Setting null sound device in PJSUA library')
                        	lib.set_null_snd_dev()
	
                	except pj.Error, e:
                        	logger.error('Lib Initialization error: %s', e)

			try:
            			logger.debug('Starting PJSUA library.')
				lib.start()
			except pj.Error, e:
                        	logger.error('Error starting pjsua library:i %s', e)

	def disconnect(self):
		try:
			logger.info('Disconnecting')
           		pj.Lib.instance().destroy()
		except pj.Error, e:
			logger.error('Error disconnecting SIP device: %s',e)

	
	def connect(self):

		logger.info('Connecting SIP device.')
		lib = pj.Lib.instance()
			
		self._login()
		self._authenticate()

		## Transport / Listener
                try:
			logger.debug('Creating transport...')
                        tr = lib.create_transport(pj.TransportType.TLS, pj.TransportConfig(random.randint(1024, 64 * 1024),'0.0.0.0'))
			logger.debug('Transport created. Type:%s, description:%s, is_reliable:%s, is_secure:%s, is_datagram:%s, host:%s, port:%s, ref_cnt:%s',tr.info().type,tr.info().description, tr.info().is_reliable,tr.info().is_secure, tr.info().is_datagram, tr.info().host, tr.info().port, tr.info().ref_cnt)
                except pj.Error, e:
                        logger.error('Error creating transport:', e)

		## SIP Account
		logger.debug('Creating sip account')
                acc_cfg = pj.AccountConfig()
                acc_cfg.id = '"{0}" <sip:{1}@{2}>'.format(self._sip_name, self._sip_username, self._sip_domain)
                acc_cfg.reg_uri = "sip:"+self._sip_domain
                acc_cfg.proxy.append(self._sip_proxy)
                acc_cfg.auth_cred = [ AuthCred("*", self._msisdn, self._sip_pass) ]

		try:
                        acc_cb = MyAccountCallback()
			logger.debug('Account Data: %s',acc_cfg.__dict__)
                        self._acc = lib.create_account(acc_cfg, set_default=True, cb=acc_cb)
			sleep(3.0)

                except pj.Error, e:
                        logger.error('Error creating account:', e)

		logger.info('Connected')

	def _authenticate(self):
		user_agent = config.get('SIP_CFG','user_agent')
		url = config.get('SIP_CFG','url_auth')

                _auth= b64encode('%s:%s' % (self._sip_user_id,self._sip_pass))
                headers = {'Authorization': 'Basic ' + _auth,
                        'User-Agent': user_agent,
                        'Content-Type': "application/json;charset=UTF-8"}

		logger.info('Authenticating user')
                response = requests.post(url, None, headers=headers)
		params = json.loads(response.content)
		logger.debug('Authentication server answer: %s',params)

		self._validToken = str(params['access_token'])

        def _login(self):
		self._msisdn = ast.literal_eval(config.get('SIP_CREDENTIALS',self._user))['msisdn']
		password = ast.literal_eval(config.get('SIP_CREDENTIALS',self._user))['password']
		url = config.get('SIP_CFG','url_login')
		user_agent = config.get('SIP_CFG','user_agent')

                _auth = b64encode('%s:%s' % (self._msisdn, password))
                headers = {'Authorization': 'Basic ' + _auth,
                        'User-Agent': user_agent,
                        'Content-Type': "application/json;charset=UTF-8"}

		logger.info('Loging user')
                response = requests.post(url, None, headers=headers)
		params = json.loads(response.content)
		logger.debug('Login server answer: %s',params)

                self._sip_pass = str(params['user']['password'])
                self._sip_name = str(params['user']['screen_name'])
                self._sip_user_id = str(params['user']['user_id'])
                self._sip_username = str(params['config']['sip']['username'])
                self._sip_domain = str(params['config']['sip']['domain'])
                self._sip_proxy = str(params['config']['sip']['proxy'])
                self._sip_pstnDomain = str(params['config']['sip']['pstn_domain'])

	def send_sms(self, destination, content, content_type='text/plain'):
                uri = str('sip:'+str(destination)+'@'+self._sip_pstnDomain)
                to = str('sip:00'+str(destination)+'@'+self._sip_pstnDomain)

		logger.info('Adding buddy [%s] to user [%s]',uri,self._user)
                buddy = self._acc.add_buddy(uri, cb=BuddyCallback())
		#buddy2 = self._acc.add_buddy(uri, request_uri=to, cb=BuddyCallback())

		logger.info('Sending IM to buddy [%s] from user[%s]',uri,self._user)
                buddy.send_pager(content, content_type=content_type)


        def call(self, destination):
                uri = 'sip:'+str(destination)+'@'+str(self._sip_pstnDomain)
		logger.info('Making call to URI: %s',uri)
                self._acc.make_call(uri, cb=MyCallCallback())




## Aux functions
def log_cb(level, str, len):
    logger.debug(str.strip())

class MyCallCallback(pj.CallCallback):
    	""" Callback to receive events from Call """

    	def __init__(self, call=None):
        	pj.CallCallback.__init__(self, call)

	def on_dtmf_digit(self, digits):
		logger.info('DTMF Tones received: %s',digits)

    	def on_state(self):
        	""" Notification when call state has changed """
		logger.info('Call status has changed. contact:%s, remote_uri:%s, remote_contact:%s, sip_call_id:%s, state_text:%s, last_code:%s, last_reason:%s, call_time:%s, total_time:%s', self.call.info().contact, self.call.info().remote_uri, self.call.info().remote_contact, self.call.info().sip_call_id, self.call.info().state_text, self.call.info().last_code, self.call.info().last_reason, self.call.info().call_time, self.call.info().total_time)


    	def on_media_state(self):
        	if self.call.info().media_state == pj.MediaState.ACTIVE:
            		# Connect the call to sound device
            		call_slot = self.call.info().conf_slot
            		pj.Lib.instance().conf_connect(call_slot, 0)
            		pj.Lib.instance().conf_connect(0, call_slot)
            		logger.info('Media is now active')
        	else:
            		logger.info('Media is inactive')


class AuthCred(object):
    def __init__(self, realm="*", username="", passwd="", scheme="Digest", passwd_type=0):
        self.scheme = scheme
        self.realm = realm
        self.username = username
        self.passwd_type = passwd_type
        self.passwd = passwd

class BuddyCallback(pj.BuddyCallback):
    def __init__(self, buddy=None):
        pj.BuddyCallback.__init__(self, buddy)

    def on_pager(self, mime_type, body):
        logger.info('on_pager %s %s %s', self.buddy, mime_type, body)
        #self.listener.on_message('MESSAGE', self.buddy.info().uri, mime_type, body, [])

    def on_pager_status(self, body, im_id, code, reason):
        logger.info('on_pager_status %s %s %s', code, self.buddy, body)
        self.buddy.delete()



class MyAccountCallback(pj.AccountCallback):
    	def __init__(self, account=None):
        	pj.AccountCallback.__init__(self, account)

    	def on_incoming_call(self, call):
		logger.info('New call incoming, contact:%s, remote_uri:%s, sip_call_id:%s, state_text:%s, last_code:%s, last_reason:%s, call_time:%s, total_time:%s', call.info().contact, call.info().remote_uri, call.info().sip_call_id, call.info().state_text, call.info().last_code, call.info().last_reason, call.info().call_time, call.info().total_time)
        	my_cb = MyCallCallback()
        	call.set_callback(my_cb)
		sleep(2)
		logger.info('Answering call %s', call.info().sip_call_id)
		call.answer()
		sleep(1)
		call.dial_dtmf('1234567890')
		logger.info('sending tones')


    	def on_reg_state(self):
        	logger.info("Registration status has changed. status= %s ( %s )", self.account.info().reg_status, self.account.info().reg_reason)

	def on_pager(self, from_uri, contact, mime_type, body):
		logger.info('New IM received. from: %s, body: %s',from_uri,body)


if __name__ == '__main__':
	
	#logging.basicConfig(level=logging.DEBUG)
	logging.basicConfig(level=logging.INFO)

	disp1 = dispsip()
	sleep (1)
	disp1.connect()
	disp1.send_sms('34699697868','HOLA')
	disp1.send_sms('447730520578','HOLA')
	sleep(3)
	disp1.call('0034699697868')
	sleep(5)
	disp1.disconnect()

	print "FIN"
