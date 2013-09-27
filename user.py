##
## Class User
##
from time import sleep
import logging
import dispsip
import dispgsm
#import dispgps

class user:
	def __init__(self, user_code,sip=True,gsm=True,gps=False):
		self.logger = logging.getLogger(user_code)
		#self._config = ConfigParser.ConfigParser()
                #self._config.read('./config.cfg')
		self.user_code=user_code
		self.logger.info('Initializing device for user:%s sip:%s gsm:%s',user_code,sip,gsm)
		self.metrics={}
		self.metrics[self.user_code]={}
		if sip:
			self._dispsip = dispsip.dispsip(self)
			self.metrics[user_code]['sip']=[]
		if gsm:
			self._dispgsm = dispgsm.dispgsm(self)
			self.metrics[user_code]['gsm']=[]
		#self._dispgps = dispgps

	def start(self,dispsip=True,dispgsm=True,dispgps=False):
		self.logger.info('Connecting devices... sip:%s, gsm:%s',dispsip,dispgsm)
		if dispsip:
			self.logger.info('Connecting SIP device')
			self._dispsip.connect()
		if dispgsm:
			self.logger.info('Connecting GSM device')
			self._dispgsm.connect()
		#if dispgps:
			#self._dispgps.connect()

	def stop(self ,dispsip=True,dispgsm=True,dispgps=False):

		self.logger.info('Stoping devices')
                if dispsip:
                        self.logger.info('Stoping SIP device')
                        self._dispsip.disconnect()
                if dispgsm:
                        self.logger.info('Stoping GSM device')
                        self._dispgsm.disconnect()
                #if dispgps:
                        #self._dispgps.connect()

	def sip_dial(self, destination):
		self._dispsip.dial(destination)

	def send_sip_sms(self, destination, content):
		self._dispsip.send_sms(destination, content)

	def gsm_dial(self, destination, dtmf=None):
		self._dispgsm.dial(destination, dtmf)

	def send_gsm_sms(self, destination, content=None):
		self._dispgsm.send_sms(destination, content)

	def get_metrics(self,sip=True,gsm=True,gps=False):
		if sip:
			self.metrics[self.user_code]['sip'].append(self._dispsip.metrics)
		if gsm:
			self.metrics[self.user_code]['gsm'].append(self._dispgsm.metrics)
	
		self.logger.debug('Returning metrics %s',self.metrics)
		return self.metrics

	def user_sms_handler(self, device):
		self.logger.info('IM/SMS recived on user %s through device: %s',self.user_code,device)

	def user_call_handler(self, device):
		self.logger.info('Call recived on user %s through device: %s',self.user_code,device)


if __name__ == '__main__':


        FORMAT = '%(asctime)-15s %(name)s %(levelname)s %(message)s'
        logging.basicConfig(level=logging.INFO,format=FORMAT)
	logger = logging.getLogger('main')

	u1 = user('user1')
	logger.info('user1 created')
	u2 = user('user2')
	logger.info( 'Users created')
	u1.start(dispsip=True,dispgsm=False)
	u2.start(dispsip=False,dispgsm=True)
	sleep (5)

	u2.gsm_dial('00447730520578')
	sleep(5)

	u2.send_gsm_sms('00447730520578','Test GSM to SIP')
	sleep(20)

	u1.stop(dispsip=True,dispgsm=False)
	u2.stop(dispsip=False,dispgsm=True)
