##
## Class GSM device
##

from __future__ import print_function
from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import InterruptedException
import sys, time, logging
import ConfigParser
import ast


class dispgsm:

	_user=None

	def __init__(self, user):

		#print 'User:', user.user_code

		dispgsm._user=user
		self.logger = logging.getLogger('device.'+user.user_code+'.dispgsm')
		self.logger.info('Initializing GSM device %s',user.user_code)

		self._config = ConfigParser.ConfigParser()
                self._config.read('./config.cfg')

		self._msisdn = ast.literal_eval(self._config.get('GSM_CREDENTIALS',user.user_code))['msisdn']
                self._pin = ast.literal_eval(self._config.get('GSM_CREDENTIALS',user.user_code))['pin']
		self._port = ast.literal_eval(self._config.get('GSM_CREDENTIALS',user.user_code))['port']
		self._baudrate = ast.literal_eval(self._config.get('GSM_CREDENTIALS',user.user_code))['baudrate']
		self._modem = GsmModem(self._port, self._baudrate, incomingCallCallbackFunc=dispgsm.handleIncomingCall, smsReceivedCallbackFunc=dispgsm.handleSms)
		#self._modem.smsTextMode = False
		


	def connect(self):
		self.logger.info('Connecting GSM modem...')
		#self._modem.connect()
		self._modem.connect(self._pin)
		self.logger.info('Waiting for network coverage...')
		self._modem.waitForNetworkCoverage(30)
		self.logger.info('GSM Device ready to use.')
		#try:
			# Specify a (huge) timeout so that it essentially blocks indefinitely, but still receives CTRL+C interrupt signal
			#self._modem.rxThread.join(2**31) 
		#finally:
			#self._modem.close()
	def disconnect(self):
		self.logger.info('Disconnecting modem...')
		self._modem.close()
		self.logger.info('Disconnected')

	def send_sms(self, destination, text, waitForDeliveryReport=False, deliveryTimeout=15):
		self.logger.info('Sending SMS with text:%s',text)
		self._modem.sendSms(destination, text, waitForDeliveryReport, deliveryTimeout)
		self.logger.info('SMS sent')

	def dial(self, destination, dtmf='1234567890'):
		self.logger.info('Calling number %s',destination)
                call = self._modem.dial(destination)
                wasAnswered = False
                while call.active:
                        if call.answered:
                                wasAnswered = True
                                self.logger.info('Call has been answered; waiting a while...')
                                # Wait for a bit - some older modems struggle to send DTMF tone immediately after answering a call
                                time.sleep(3.0)
                                self.logger.info('Playing DTMF tones: %s',dtmf)
                                try:
                                        if call.active: # Call could have been ended by remote party while we waited in the time.sleep() call
                                                call.sendDtmfTone(dtmf)
						self.logger.info('DTMF tones sent')
						time.sleep(10)
                                except InterruptedException as e:
                                        # Call was ended during playback
                                        self.logger.info('DTMF playback interrupted: {0} ({1} Error {2})'.format(e, e.cause.type, e.cause.code))
                                except CommandError as e:
                                        self.logger.error('DTMF playback failed: {0}'.format(e))
                                finally:
                                        if call.active: # Call is still active
                                                self.logger.info('Hanging up call...')
                                                call.hangup()
                                        else: # Call is no longer active (remote party ended it)
                                                self.logger.info('Call has been ended by remote party')
                        else:
                                # Wait a bit and check again
                                 time.sleep(0.5)
                if not wasAnswered:
                        self.logger.info('Call was not answered by remote party')
                self.logger.info('Call finished')


	def handleIncomingCall(call):
		logger = logging.getLogger('device.'+dispsip._user.user_code+'.dispgsm')
    		if call.ringCount == 1:
        		logger.info('Incoming call from:', call.number)
    		elif call.ringCount >= 2:
            		logger.info('Answering call and playing some DTMF tones...')
            		call.answer()
            		# Wait for a bit - some older modems struggle to send DTMF tone immediately after answering a call
            		time.sleep(20.0)
            		try:
                		call.sendDtmfTone('9515999955951')
            		except InterruptedException as e:
                		# Call was ended during playback
                		logger.info('DTMF playback interrupted: {0} ({1} Error {2})'.format(e, e.cause.type, e.cause.code))
            		finally:
                		if call.answered:
                    			logger.info('Hanging up call.')
                    			call.hangup()
    		else:
        		logger.info(' Call from {0} is still ringing...'.format(call.number))


	def handleSms(sms):
		logger = logging.getLogger('device.'+dispsip._user.user_code+'.dispgsm')
		logger.info(u'== SMS message received ==\nFrom: {0}\nTime: {1}\nMessage:\n{2}\n'.format(sms.number, sms.time, sms.text))
		#sms.reply(u'SMS received: "{0}{1}"'.format(sms.text[:20], '...' if len(sms.text) > 20 else ''))



