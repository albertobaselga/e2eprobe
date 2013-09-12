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
		self._user=user_code
		if not pj.Lib.instance():
			lib = pj.Lib()
			my_ua_cfg = pj.UAConfig()
                	my_ua_cfg.user_agent = config.get('SIP_CFG','user_agent')
                	my_ua_cfg.max_calls = 5

                	my_media_cfg = pj.MediaConfig()
                	my_media_cfg.enable_ice = True
                	#my_media_cfg.channel_count = 0

                	try:
                        	lib.init(log_cfg=pj.LogConfig(level=log_level, callback=log_cb), ua_cfg=my_ua_cfg, media_cfg=my_media_cfg)
                        	lib.set_null_snd_dev()
	
                	except pj.Error, e:
                        	print 'Lib Initialization error:', e

			try:
            			lib.start()
			except pj.Error, e:
                        	print 'Error starting pjsua library:', e
	def disconnect(self):
           	pj.Lib.instance().destroy()

	
	def connect(self):
		lib = pj.Lib.instance()
		
		self._login()
		self._authenticate()

		## Transport / Listener
                try:
                        lib.create_transport(pj.TransportType.TLS, pj.TransportConfig(random.randint(1024, 64 * 1024),'0.0.0.0'))
                except pj.Error, e:
                        print 'Error creating transport:', e

		## SIP Account
                acc_cfg = pj.AccountConfig()
                acc_cfg.id = '"{0}" <sip:{1}@{2}>'.format(self._sip_name, self._sip_username, self._sip_domain)
                acc_cfg.reg_uri = "sip:"+self._sip_domain
                #acc_cfg.user_agent = 'GConnect/1.0 (P; Apple; iPhone; iPhone OS; 5.1;)(7e8049ad-f919-3290-858f-7f6b7ee8ae2c)'
                acc_cfg.proxy.append(self._sip_proxy)
                acc_cfg.auth_cred = [ AuthCred("*", self._msisdn, self._sip_pass) ]

		try:
                        acc_cb = MyAccountCallback()
                        self._acc = lib.create_account(acc_cfg, set_default=True, cb=acc_cb)
			sleep(3.0)

                except pj.Error, err:
                        print 'Error creating account:', err

		logger.info('Connected')

	def _authenticate(self):
		user_agent = config.get('SIP_CFG','user_agent')
		url = config.get('SIP_CFG','url_auth')

                _auth= b64encode('%s:%s' % (self._sip_user_id,self._sip_pass))
                headers = {'Authorization': 'Basic ' + _auth,
                        'User-Agent': user_agent,
                        'Content-Type': "application/json;charset=UTF-8"}

                response = requests.post(url, None, headers=headers)
		params = json.loads(response.content)

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

                response = requests.post(url, None, headers=headers)
		params = json.loads(response.content)

                self._sip_pass = str(params['user']['password'])
                self._sip_name = str(params['user']['screen_name'])
                self._sip_user_id = str(params['user']['user_id'])
                self._sip_username = str(params['config']['sip']['username'])
                self._sip_domain = str(params['config']['sip']['domain'])
                self._sip_proxy = str(params['config']['sip']['proxy'])
                self._sip_pstnDomain = str(params['config']['sip']['pstn_domain'])

	def send_sms(self, destination, content, content_type='text/plain;charset=utf-8'):
                header = [('Comm-Notifications', 'delivered, displayed'),
                        ('Comm-ID','1234567890'),
                        ('Comm-Logging', 'on'),
                        ('Comm-Type', 'text')]
                uri = "sip:"+str(destination)+"@"+self._sip_pstnDomain
                buddy = self._acc.add_buddy(uri, cb=BuddyCallback())
                buddy.send_pager(content, content_type=content_type, hdr_list=header)

        def call(self, destination):
                header = [('Comm-Notifications', 'delivered, displayed'),
                        #('Comm-ID',DEVICEID),
                        #('Comm-ID','18916357-4f52-400f-99be-4c94cf0996bb'),
                        ('Comm-Logging', 'on'),
                        ('Content-Type', 'application/sdp'),
                        ('Comm-Type', 'call')]

                uri = "sip:"+str(destination)+"@"+self._sip_pstnDomain
                #self._acc.make_call(uri, hdr_list=header, cb=MyCallCallback())
                self._acc.make_call(uri, cb=MyCallCallback())



## Aux functions
def log_cb(level, str, len):
    logger.debug(str.strip())

class MyCallCallback(pj.CallCallback):
    """ Callback to receive events from Call """

    def __init__(self, call=None):
        pj.CallCallback.__init__(self, call)

    def on_state(self):
        """ Notification when call state has changed """
        logger.info('on_state %s', self.call)
        logger.info("Call is %s", self.call.info().state_text)
        logger.info("last code %s", self.call.info().last_code)
        logger.info("(%s)", self.call.info().last_reason)

    def on_media_state(self):
        """ Notification when call's media state has changed. """
        logger.info('on_media_state %s', self.call)
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            # Connect the call to sound device
            call_slot = self.call.info().conf_slot
            pj.Lib.instance().conf_connect(call_slot, 0)
            pj.Lib.instance().conf_connect(0, call_slot)


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
        my_cb = MyCallCallback()
        call.set_callback(my_cb)

    #def on_incoming_call(self, call):
        #call.hangup(501, "Sorry, not ready to accept calls yet")

    def on_reg_state(self):
        logger.info("Registration complete, status= %s ( %s )",
                    self.account.info().reg_status,
                    self.account.info().reg_reason)


if __name__ == '__main__':
	
	logging.basicConfig(level=logging.INFO)

	disp1 = dispsip()
	sleep (1)
	disp1.connect()
	sleep(3)
	disp1.send_sms('34699697868','HOLA')
	sleep(3)
	disp1.call(34699697868)
	sleep(5)
	disp1.disconnect()

	print "FIN"
