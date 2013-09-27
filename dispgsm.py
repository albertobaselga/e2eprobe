##
## Class GSM device
##

from __future__ import print_function
from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import InterruptedException
import sys, time, logging
import ConfigParser
import ast
import datetime
import random


class dispgsm:

	_user=None
	metrics={}

	def __init__(self, user):

		dispgsm._user=user
		self.logger = logging.getLogger(user.user_code+'.dispgsm')
		self.logger.info('Initializing GSM device %s',user.user_code)

		self._config = ConfigParser.ConfigParser()
                self._config.read('./config.cfg')

		self._msisdn = ast.literal_eval(self._config.get('GSM_CREDENTIALS',user.user_code))['msisdn']
                self._pin = ast.literal_eval(self._config.get('GSM_CREDENTIALS',user.user_code))['pin']
		self._port = ast.literal_eval(self._config.get('GSM_CREDENTIALS',user.user_code))['port']
		self._baudrate = ast.literal_eval(self._config.get('GSM_CREDENTIALS',user.user_code))['baudrate']
		self._modem = GsmModem(self._port, int(self._baudrate), incomingCallCallbackFunc=dispgsm.handleIncomingCall, smsReceivedCallbackFunc=dispgsm.handleSms, smsStatusReportCallback=dispgsm.handleSmsDeliveryReport)
		#self._modem.smsTextMode = False
		


	def connect(self):
		self.logger.info('Connecting GSM modem...')
		#self._modem.connect()
		self._modem.connect(self._pin)
		self.logger.info('Waiting for network coverage...')
		try:
			self._modem.waitForNetworkCoverage(30)
		except TimeoutException:
        		self.logger.error('Network signal strength is not sufficient, please adjust modem position/antenna and try again.')
			self.disconnect()

                self.metrics['handled_sms']=[]
                self.metrics['handled_call']=[]
		self.metrics['send_sms']=[]
		self.metrics['dial_call']=[]
		self.logger.info('GSM Device ready to use.')

	def disconnect(self):
		self.logger.info('Disconnecting modem...')
		self._modem.close()
		self.logger.info('Disconnected')

	def send_sms(self, destination, text, waitForDeliveryReport=True, deliveryTimeout=15):
		if text==None:
			text =  str(random.randint(1000000000, 9999999999))

		self.logger.info('Sending SMS with text:%s',text)
		m ={}
		m['sms_text'] = text
		m['sms_delivery_timeout'] = deliveryTimeout
		m['sms_sent_time'] = str(datetime.datetime.now())
		try:
			sms = self._modem.sendSms(destination, text, waitForDeliveryReport, deliveryTimeout)
                	self.logger.info('Message sent with delivery report status:%s reference:%s',sms.status,sms.reference)
			if sms.status==0:
				m['sms_status'] = 'ENROUTE'
			elif sms.status==1:
				m['sms_status'] = 'DELIVERED'
			elif sms.status==2:
				m['sms_status'] = 'FAILED'
			else:
				m['sms_status'] = 'ERROR'
		except TimeoutException:
			self.logger.warning('Fail to deliver message: the send operation timed out')
		m['sms_end'] = str(datetime.datetime.now())
		self.metrics['send_sms'].append(m)


	def dial(self, destination, dtmf):
		if dtmf==None:
			dtmf = str(random.randint(1000000000, 9999999999))
		self.logger.info('Calling number %s and sending DTMF:%s',destination,dtmf)
		m = {}
		m['dial_dtmf'] = dtmf
		m['dial_start'] = str(datetime.datetime.now())
                call = self._modem.dial(destination)
                wasAnswered = False
                while call.active:
                        if call.answered:
                                wasAnswered = True
                                self.logger.info('Call has been answered; waiting a while...')
				m['dial_answered'] = str(datetime.datetime.now())
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
						m['dial_hangup'] = str(datetime.datetime.now())
                                                call.hangup()
                                        else: # Call is no longer active (remote party ended it)
                                                self.logger.info('Call has been ended by remote party')
                        else:
                                # Wait a bit and check again
                                 time.sleep(0.5)
                if not wasAnswered:
                        self.logger.info('Call was not answered by remote party')
                self.logger.info('Call finished')
		m['dial_end'] = str(datetime.datetime.now())
		self.metrics['dial_call'].append(m)



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

	def handleSmsDeliveryReport(sms):
		logger = logging.getLogger('device.'+dispsip._user.user_code+'.dispgsm')
		logger.info('Delivery report received status:%s reference:%s timeSent:%s timefinalized:%s deliveryStatus:%s',sms.status,sms.reference,sms.timeSent,sms.timeFinalized,sms.deliveryStatus)

