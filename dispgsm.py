##
## Class GSM device
##

from __future__ import print_function
from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import InterruptedException
import sys, time, logging

class dispgsm:


	def __init__(self, msisdn, pin, port, baudrate):
		self._msisdn = msisdn
		self._pin = pin
		self._port = port
		self._baudrate = baudrate
		self._modem = GsmModem(self._port, self._baudrate, incomingCallCallbackFunc=handleIncomingCall, smsReceivedCallbackFunc=handleSms)
		#self._modem.smsTextMode = False


	def connect(self):
		print('Initializing modem...')
		self._modem.connect(self._pin)
		print('Waiting for network coverage...')
		self._modem.waitForNetworkCoverage(30)
		print('Ready')
		#try:
			# Specify a (huge) timeout so that it essentially blocks indefinitely, but still receives CTRL+C interrupt signal
			#self._modem.rxThread.join(2**31) 
		#finally:
			#self._modem.close()
	def disconnect(self):
		print('Disconnecting modem...')
		self._modem.close()
		print('Disconnected')

	def sendSMS(self, destination, test, waitForDeliveryReport=False, deliveryTimeout=15):
		print('Sending SMS...')
		self._modem.sendSms(destination, text, waitForDeliveryReport, deliveryTimeout)
		print('SMS sent')

	def dial(self, destination):
                call = self._modem.dial(destination)
                wasAnswered = False
                while call.active:
                        if call.answered:
                                wasAnswered = True
                                print('Call has been answered; waiting a while...')
                                # Wait for a bit - some older modems struggle to send DTMF tone immediately after answering a call
                                time.sleep(3.0)
                                print('Playing DTMF tones...')
                                try:
                                        if call.active: # Call could have been ended by remote party while we waited in the time.sleep() call
                                                call.sendDtmfTone('9515999955951')
                                except InterruptedException as e:
                                        # Call was ended during playback
                                        print('DTMF playback interrupted: {0} ({1} Error {2})'.format(e, e.cause.type, e.cause.code))
                                except CommandError as e:
                                        print('DTMF playback failed: {0}'.format(e))
                                finally:
                                        if call.active: # Call is still active
                                                print('Hanging up call...')
                                                call.hangup()
                                        else: # Call is no longer active (remote party ended it)
                                                print('Call has been ended by remote party')
                        else:
                                # Wait a bit and check again
                                 time.sleep(0.5)
                if not wasAnswered:
                        print('Call was not answered by remote party')
                print('Done.')
                self._modem.close()


def handleIncomingCall(call):
    		if call.ringCount == 1:
        		print('Incoming call from:', call.number)
    		elif call.ringCount >= 2:
            		print('Answering call and playing some DTMF tones...')
            		call.answer()
            		# Wait for a bit - some older modems struggle to send DTMF tone immediately after answering a call
            		time.sleep(20.0)
            		try:
                		call.sendDtmfTone('9515999955951')
            		except InterruptedException as e:
                		# Call was ended during playback
                		print('DTMF playback interrupted: {0} ({1} Error {2})'.format(e, e.cause.type, e.cause.code))
            		finally:
                		if call.answered:
                    			print('Hanging up call.')
                    			call.hangup()
    		else:
        		print(' Call from {0} is still ringing...'.format(call.number))


def handleSms(sms):
		print(u'== SMS message received ==\nFrom: {0}\nTime: {1}\nMessage:\n{2}\n'.format(sms.number, sms.time, sms.text))
		#sms.reply(u'SMS received: "{0}{1}"'.format(sms.text[:20], '...' if len(sms.text) > 20 else ''))



