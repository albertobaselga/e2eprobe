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

def run_waiting(user_code):
	logger.info('Starting function %s',user_code)
	u = user.user(user_code,sip=True,gsm=False)
	u.start(dispsip=True,dispgsm=False)
	sleep(60)
	u.stop(dispsip=True,dispgsm=False)

def run_active(user_code):
	logger.info('Starting function %s',user_code)
	u = user.user(user_code,sip=False,gsm=True)
	u.start(dispsip=False,dispgsm=True)
	sleep (10)
        u.gsm_dial('00447730520578')
        sleep(5)
        u.send_gsm_sms('00447730520578','Test GSM to SIP')
        sleep(20)
	u.stop(dispsip=False,dispgsm=True)

threads = []

FORMAT = '%(asctime)-15s %(name)s %(levelname)s %(message)s'
#logging.basicConfig(level=logging.DEBUG,format=FORMAT)
logging.basicConfig(level=logging.INFO,format=FORMAT)
logger = logging.getLogger('device')


logger.info('Starting test')
#user_code='user1'
#thread1 = threading.Thread(target=run_waiting,args=(user_code,))
#thread1.start()
user_code='user2'
thread2 = threading.Thread(target=run_active,args=(user_code,))
thread2.daemon = True
thread2.start()
user_code='user1'
run_waiting(user_code)
#threads.append(thread1)
threads.append(thread2)

# to wait until all three functions are finished

logger.info('Waiting tests to finish...')

for thread in threads:
    thread.join()

logger.info('Test Complete. Results:')
