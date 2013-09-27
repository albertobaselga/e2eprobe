##
## Class Test
##

#class test:
	#def __init__(self, ini_timestamp, origin, destination):
		#self._ini_timestamp = ini_timestamp
		#self._orig = origin
		#self._dest = destination	

import threading
import user
import logging
from time import sleep
import ConfigParser
import ast
import json


class test:
	results=[]

	def __init__(self,config_file, test_name): 
		self.logger = logging.getLogger(test_name)
		self.logger.info('Importing test configuration file: %s',config_file)
		self._config = ConfigParser.ConfigParser()
                self._config.read(config_file)
		self._test_name = test_name

	def add_metrics(self, metrics):
		self.logger.info('%s',metrics)
		self.results.append(metrics)

	def _run_receiver(self):
		self.logger.info('Starting receiver user thread')
		user_code = self._config.get(self._test_name,'receiver_user')
		user_sip = ast.literal_eval(self._config.get(self._test_name,'receiver_user_devices'))['sip']
		user_gsm = ast.literal_eval(self._config.get(self._test_name,'receiver_user_devices'))['gsm']
		waiting_time = self._config.get(self._test_name,'receiver_user_waiting_time')
		
		self.logger.info('Initalizing receiver user: user_code:%s, sip:%s, gsm:%s, waiting_time:%s s',user_code,user_sip,user_gsm,waiting_time)
		u = user.user(user_code,sip=user_sip,gsm=user_gsm)

		self.logger.info('Starting receiver user')
		u.start(dispsip=user_sip, dispgsm=user_gsm)

		self.logger.info('Entering reveicer user in sleeping mode for %s seconds',waiting_time)
		sleep(float(waiting_time))

		self.logger.info('Receiver waiting time finished. Collecting receiver metrics and stoping user')
		self.add_metrics(u.get_metrics(sip=user_sip,gsm=user_gsm))
		u.stop(dispsip=user_sip, dispgsm=user_gsm)

	def _run_issuer(self):
                self.logger.info('Starting issuer user thread')
                user_code = self._config.get(self._test_name,'issuer_user')
                user_sip = ast.literal_eval(self._config.get(self._test_name,'issuer_user_devices'))['sip']
                user_gsm = ast.literal_eval(self._config.get(self._test_name,'issuer_user_devices'))['gsm']
		user_actions = self._config.get(self._test_name,'issuer_user_actions')

                self.logger.info('Initalizing issuer user: user_code:%s, sip:%s, gsm:%s, actions:%s',user_code,user_sip,user_gsm,user_actions)
                u = user.user(user_code,sip=user_sip,gsm=user_gsm)

                self.logger.info('Starting issuer user')
                u.start(dispsip=user_sip, dispgsm=user_gsm)
		sleep(10)

		for act in user_actions.split(','):
			if act == 'gsm_dial':
				self.logger.info('Launching GSM dial action')
				u.gsm_dial('00447730520578')
				sleep(10)
			elif act == 'gsm_sms':
				self.logger.info('Launching GSM sms action')
				u.send_gsm_sms('00447730520578')
				sleep(10)

		self.logger.info('Issuer actions finished. Collecting issuer metrics and stoping user')
		self.add_metrics(u.get_metrics(sip=user_sip,gsm=user_gsm))
		u.stop(dispsip=user_sip, dispgsm=user_gsm)


	def run(self):
		threads = []
	
		self.logger.info('Running test %s',self._test_name)
		thread1 = threading.Thread(target=self._run_issuer)
		thread1.daemon = True
		thread1.start()
		threads.append(thread1)
		
		#thread2 = threading.Thread(target=self._run_receiver)
		#thread2.daemon = True
		#thread2.start()
		#threads.append(thread2)
		self._run_receiver()

		for thread in threads:
    			thread.join()
		self.logger.info('Test %s finished. Results:',self._test_name)
		print json.dumps(self.results, indent=4)

if __name__ == '__main__':

	FORMAT = '%(asctime)-15s %(name)s %(levelname)s %(message)s'
	#logging.basicConfig(level=logging.DEBUG,format=FORMAT)
	logging.basicConfig(level=logging.INFO,format=FORMAT)


	config = ConfigParser.ConfigParser()
        config.read('./test.cfg')

	for test_name in config.sections():
		t = test('./test.cfg',test_name)
		t.run()

