##
## Class User
##
from time import sleep
import logging
import dispsip
import dispgsm
#import dispgps

class user:
	def __init__(self, user_code):
		#self._config = ConfigParser.ConfigParser()
                #self._config.read('./config.cfg')

		self._dispsip = dispsip.dispsip(user_code=user_code)
		#self._dispgsm = dispgsm(user_code=user_code)
		#self._dispgps = dispgps

	def start(self):
		self._dispsip.connect()
		#self._dispgsm.connect()

	def stop(self):
		self._dispsip.disconnect()

	def send_sip_sms(self, destination, content):
		self._dispsip.send_sms(destination, content)

	def send_gsm_sms(self, destino):
		self._dispgsm.send_sms(destination, content)


def user_call_handler(device):
	print 'SIIIIIIIIIIIIIIIIIIIIIIIII %s',device


if __name__ == '__main__':


        FORMAT = '%(asctime)-15s %(name)s %(levelname)s %(message)s'
        logging.basicConfig(level=logging.INFO,format=FORMAT)

	u1 = user('user1')
	u1.start()
	sleep (300)
	u1.disconnect()
