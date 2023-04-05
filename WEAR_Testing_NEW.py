#Joe Snider
#7/14
#
#read in the treadmill foreplate data
from socket import socket, AF_INET, SOCK_STREAM
import json
import time
import viztask
import viz
import u6
import math
import viztask
import numpy as np
import text_log
import time
import logutil

import sys
import viz
import vizact
import vizinfo

import steamvr
import steve 
import vizdlg,vizshape
import math,random

#import labJack_u6
#import Illini_lean_slider

import string
#import fixation_cross



logfile10 = open("EMGtime.txt", "w")
logfile10.write("begintime           endtime")
logfile10.flush()



#logfile11 = open("clinical_module_time.txt", "w")
#logfile11.write("begintime           endtime")
#logfile11.flush()

logfile12 = open("treadmill_v.txt", "w")
logfile12.write("TreadmillV           Time")
logfile12.flush()

###########
#INIT VIZ##
###########
	
vizshape.addAxes()
viz.setMultiSample(2)
viz.go() #Main method call 

#Initialize visuals 
viz.clearcolor(0.5,0.5,0.5) 
#ground = viz.addChild('ground_grass.osgb') 
viz.MainView.setPosition([0,1.8,-7])

#######
##LOG##
#######
eventLogM = text_log.TextLog("position of the sensors\n")
logM = text_log.TextLog("")
loggerM = logutil.TrialLogger()
loggerM.addSimpleSensor(eventLogM, 'events mocap', 1000)
loggerM.addSimpleSensor(logM, 'notes mocap', 1000)


##################################################
# send pulses to EEG
##################################################
parallel_port = 0xC050
	
#import random
#import sendPulse
#S1 = sendPulse.SendPulse(parallel_port)
#	
##time between eeg calibration pulses (approx) and 
##the spacing between the eeg timing codes
#EEG_TIMING_DELAY_LOW 	= 1
#EEG_TIMING_DELAY_HIGH 	= 10
#EEG_SPACING 			= 0.1
#EEG_TIMING_MARK 		= 1
#	
#eegfile = 'eeg_log.txt'
#EEGlogger = open(eegfile, 'w')
## sends the current viztick to the eeg and the data file
## This is called from a separate thread
#def MarkEEG():
#	while True:
#		#pause for a while
#		viz.waittime(random.randint(EEG_TIMING_DELAY_LOW, EEG_TIMING_DELAY_HIGH))
#		#send a sequence to the eeg to mark
#		recordTime = S1.generateTimeCode()
#		S1.sendPulse(EEG_TIMING_MARK)
#		EEGlogger.write(str(recordTime)+"\n")
#		EEGlogger.flush()
#		#send the rest
#		if S1.tickSplit != None:
#			for sendValIter in S1.tickSplit:
#				viz.waittime(EEG_SPACING)
#				S1.sendPulse(sendValIter)
#eegThread = viz.director( MarkEEG )

thredV=-1
lowthredV=-1

thredV1=2
lowthredV1=1

MIN_WEIGHT_NEWTONS = -100# ~20 lbs, negetive for downward gravity

LEFT_OFF_TREADMILL = viz.getEventID('LEFT_OFF_TREADMILL')
LEFT_ON_TREADMILL = viz.getEventID('LEFT_ON_TREADMILL')
RIGHT_OFF_TREADMILL = viz.getEventID('RIGHT_OFF_TREADMILL')
RIGHT_ON_TREADMILL = viz.getEventID('RIGHT_ON_TREADMILL')

class CTreadmillForcePlate():
	def __init__(self):
		self.device = u6.U6()
		print self.device.configU6()
		
		#for the labjack
		self.numChannels = 8
		self.firstChannel = 1
		self.resolutionIndex = 4
		self.gainIndex = 0
		self.settlingFactor = 0
		self.differential = False
		
		self.latestAinValues = np.array([0]*self.numChannels, dtype='float')
		self.lastForceMoments = np.array([0]*self.numChannels, dtype='float')
		self.latestForceMoments = np.array([0]*self.numChannels, dtype='float')
		self.zero = np.array([0]*self.numChannels, dtype='float')
		
		self.lastTime = 0
		self.latestTime = 0
		
		self.lastLeftOn = False
		self.latestLeftOn = False
		self.lastLeftCOP = [0, 0]
		
class CTreadmillForcePlate():
	def __init__(self):
		self.device = u6.U6()
		print self.device.configU6()
		
		#for the labjack
		self.numChannels = 8
		self.firstChannel = 1
		self.resolutionIndex = 4
		self.gainIndex = 0
		self.settlingFactor = 0
		self.differential = False
		
		self.latestAinValues = np.array([0]*self.numChannels, dtype='float')
		self.lastForceMoments = np.array([0]*self.numChannels, dtype='float')
		self.latestForceMoments = np.array([0]*self.numChannels, dtype='float')
		self.zero = np.array([0]*self.numChannels, dtype='float')
		
		self.lastTime = 0
		self.latestTime = 0
		
		self.lastLeftOn = False
		self.latestLeftOn = False
		self.lastLeftCOP = [0, 0]
		self.latestLeftCOP = [0, 0]

		self.lastRightOn = False
		self.latestRightOn = False
		self.lastRightCOP = [0, 0]
		self.latestRightCOP = [0, 0]
		
		FIOEIOAnalog = ( 2 ** self.numChannels ) - 1;
		fios = FIOEIOAnalog & (0xFF)
		eios = FIOEIOAnalog/256
		self.device.getFeedback(u6.PortDirWrite(Direction = [0, 0, 0], WriteMask = [0, 0, 15]))
		self.feedbackArguments = []
		self.feedbackArguments.append(u6.DAC0_8(Value = 125))
		self.feedbackArguments.append(u6.PortStateRead())
		for i in range(self.firstChannel, self.numChannels+self.firstChannel):
			self.feedbackArguments.append( u6.AIN24(i, self.resolutionIndex, self.gainIndex, self.settlingFactor, self.differential) )
			
		self.task = viztask.schedule(self.__update)
		self.going = True
		self.history = []
		self.recording = False
		self.latestLeftCOP = [0, 0]

		self.lastRightOn = False
		self.latestRightOn = False
		self.lastRightCOP = [0, 0]
		self.latestRightCOP = [0, 0]
		
		FIOEIOAnalog = ( 2 ** self.numChannels ) - 1;
		fios = FIOEIOAnalog & (0xFF)
		eios = FIOEIOAnalog/256
		self.device.getFeedback(u6.PortDirWrite(Direction = [0, 0, 0], WriteMask = [0, 0, 15]))
		self.feedbackArguments = []
		self.feedbackArguments.append(u6.DAC0_8(Value = 125))
		self.feedbackArguments.append(u6.PortStateRead())
		for i in range(self.firstChannel, self.numChannels+self.firstChannel):
			self.feedbackArguments.append( u6.AIN24(i, self.resolutionIndex, self.gainIndex, self.settlingFactor, self.differential) )
			
		self.task = viztask.schedule(self.__update)
		self.going = True
		self.history = []
		self.recording = False
		
		#magic numbers to turn volts into Newtons and Newton.meters
		#left is stored in first 6 (x,y,z,mx,my,mz) and right in second 6
		# 8 channels - for data need the following: 0,2,4,1,3,5
		self.M = np.array([[-505.83, -504.94 , -504.25 , -509.61 ,-506.97 , -511.85 , 0.000000 , 0.000000 ],\
			[-1476.71, -826.24 , -824.59 , -1488.39 , -181.39 , -183.10 , 0.000000 , 0.000000],\
			[416.78, 22.70 , 414.31 , 22.97 , 418.16 , 23.08 , 0.000000 , 0.000000]],dtype='float')

#	def MyTask1():
#	   while True: 
#	       yield viztask.waitKeyDown('l')
#	       print self.latestAinValues
#	viztask.schedule( MyTask1() )

	def __update(self):
		msg1 = viz.addText("", parent=viz.SCREEN, pos=(0, 0.7, 0))
		msg2 = viz.addText("", parent=viz.SCREEN, pos=(0, 0.9, 0))
		msg3 = viz.addText("", parent=viz.SCREEN, pos=(0, 0.1, 0))
		t0 = 0 #for testing
		self.device.softReset()
		yield viztask.waitTime(1)
		print "Zeroing treadmill ... ",
		self.doZero()
		print "done"
		print "Started treadmill forceplates read"
		while self.going:
			results = self.device.getFeedback( self.feedbackArguments )
			for j in range(self.numChannels):
				self.latestAinValues[j] = self.device.binaryToCalibratedAnalogVoltage(self.gainIndex, results[2+j])
			self.lastForceMoments = list(self.latestForceMoments)
			self.latestForceMoments = self.M.dot(self.latestAinValues+self.zero)
			self.lastLeftOn = self.latestLeftOn
			self.lastRightOn = self.latestRightOn
			self.lastLeftCOP = list(self.latestLeftCOP)
			self.lastRightCOP = list(self.latestRightCOP)
			self.lastTime = self.latestTime
			self.latestTime = viz.tick()
			try:
				# these need to be changed since we have single force plate
				self.latestLeftOn = (self.latestForceMoments[0] > MIN_WEIGHT_NEWTONS)
				self.latestLeftCOP[0] = -1.0*self.latestForceMoments[1]/self.latestForceMoments[0]
				self.latestLeftCOP[1] = self.latestForceMoments[2]/self.latestForceMoments[0]
				self.latestRightOn = (self.latestForceMoments[0] > MIN_WEIGHT_NEWTONS)
				self.latestRightCOP[0] = -1.0*self.latestForceMoments[1]/self.latestForceMoments[0]
				self.latestRightCOP[1] = self.latestForceMoments[2]/self.latestForceMoments[0]
			except(ZeroDivisionError):
				print "div zero caught in ForcePlate ... ignoring"
				pass
			if self.recording:
				#self.data.append([viz.tick(), [x for x in self.latestAinValues]])
				self.data.append([viz.tick(), [x for x in self.latestForceMoments]])
				
			if self.lastLeftOn and not self.latestLeftOn:
				viz.sendEvent(LEFT_OFF_TREADMILL)
			if not self.lastLeftOn and self.latestLeftOn:
				viz.sendEvent(LEFT_ON_TREADMILL)
			if self.lastRightOn and not self.latestRightOn:
				viz.sendEvent(RIGHT_OFF_TREADMILL)
			if not self.lastRightOn and self.latestRightOn:
				viz.sendEvent(RIGHT_ON_TREADMILL)
				
			#testing
			t1 = t0
			t0 = viz.tick()
#######treadmill recording
			#msg.message("%3.3fs"%(t0-t1))
			#msg3.message("%6.3f %6.3f %6.3f"%(self.latestForceMoments[0], self.latestForceMoments[1], self.latestForceMoments[2]))
			msg1.message("%6.3f %6.3f %6.3f %6.3f"%(self.latestAinValues[4], self.latestAinValues[5], self.latestAinValues[6], self.latestAinValues[7]))
			msg2.message("%6.3f %6.3f %6.3f %6.3f"%(self.latestAinValues[0], self.latestAinValues[1], self.latestAinValues[2], self.latestAinValues[3]))
#			msg1.message("%6.3f %6.3f %6.3f"%(self.latestAinValues[3], self.latestAinValues[4], self.latestAinValues[5]))
#			msg2.message("%6.3f %6.3f %6.3f"%(self.latestAinValues[0], self.latestAinValues[1], self.latestAinValues[2]))
			
#			def task0():
#				while True: 
#					yield viztask.waitTime( 1)
#					#yield viztask.waitKeyDown('v')
#					print self.latestAinValues[1]
#			viztask.schedule( task0() )
			
			
			
#			def task1():
#				while True: 
#					yield viztask.waitTime( 0.1)
#					if self.latestAinValues[1] <5:
#						print ("1")
#					else:
#						print ("detected")
#			viztask.schedule( task1() )

			#thredV=5
			#global thredV
			def detectbeginningEMG():
				#global thredV
				while True: 
					global thredV
					global lowthredV
					#thredV = 5
					yield viztask.waitTime( 0.01)
					#global thredV
					
					if self.latestAinValues[3] < thredV:
						lowthredV = -1
						print ("EMG detected")
						logfile10.write( "\n" )
						logfile10.write(str(viz.tick()))
						logfile10.write("    ")
						thredV = -10
						#lowthredV = 1
						yield viztask.waitTime( 0.01)
						#lowthredV = 1
						def detectendingEMG():
							global lowthredV

							while True:
								yield viztask.waitTime( 0.01)

								if self.latestAinValues[5]  < lowthredV:
									print ("EMG end detected")
									logfile10.write( "           " )
									print(viz.tick())
									logfile10.write(str(viz.tick()))
									lowthredV=-10
									thredV = -1
						viztask.schedule( detectendingEMG() )
					
					if lowthredV == -10:
						thredV = -1
			viztask.schedule( detectbeginningEMG() )		
	
			
			def detectbeginningclinical():
				#global thredV
				while True: 
					global thredV1
					global lowthredV1
					#thredV = 5
					yield viztask.waitTime( 0.01)
					#global thredV
					
					if self.latestAinValues[0] > thredV1:
						lowthredV1 = 1
						print ("NC detected")
						logfile11.write( "\n" )
						logfile11.write(str(viz.tick()))
						logfile11.write("    ")
						thredV1 = 10
						#lowthredV = 1
						yield viztask.waitTime( 0.01)
						#lowthredV = 1
						def detectendingclinical():
							global lowthredV1

							while True:
								yield viztask.waitTime( 0.01)
								if self.latestAinValues[0] < lowthredV1:
									print ("NC end detected")
									logfile11.write( "           " )
									logfile11.write(str(viz.tick()))
									lowthredV1=-5
									#thredV = 5
						viztask.schedule( detectendingclinical() )
					
					if lowthredV1 == -5:
						thredV1 = 2
			viztask.schedule( detectbeginningclinical() )	



			#print "%6.3f , %6.9f"%(self.latestForceMoments[0],time.time()) #time.time()
			log1 = text_log.TextLog("")
			import logutil
			logger = logutil.TrialLogger()
			logger.addSimpleSensor(log1, 'note1', 1)
			#logger.startTrial()
			#log1.Record("%6.3f %6.3f %6.3f %6.3f %6.3f %6.3f"%(self.latestAinValues[0], self.latestAinValues[1], self.latestAinValues[2], self.latestAinValues[3], self.latestAinValues[4], self.latestAinValues[5]))
			#logger.stopTrial()
			#print self.latestForceMoments[0]
			#if self.lastLeftOn:
				#msg.message("Left on")
			#elif self.lastRightOn:
				#msg.message("Right on")
			yield None
			
	def doZero(self, samples=100):
		self.zero = np.array([0]*self.numChannels, dtype='float')
		for i in range(samples):
			results = self.device.getFeedback( self.feedbackArguments )
			for j in range(self.numChannels):
				self.latestAinValues[j] = self.device.binaryToCalibratedAnalogVoltage(self.gainIndex, results[2+j])
			self.zero += self.latestAinValues
		self.zero /= -1.0*float(samples)

	
	#junk is needed for compatibility with logutil
	def startRecording(self,junk=1):
		self.clearRecording()
		self.recording = True
	def stopRecording(self):
		self.recording = False
	def dumpRecording(self,fname="recording.txt"):
		f = open(fname, 'w')
		for k in self.data:
			f.write("%10.9g "%(k[0]))
			for v in k[1]:
				f.write("%10.9g "%(v))
			f.write("\n")
	def clearRecording(self):
		self.data = []

		
if __name__ == '__main__':
#	viz.go()
#	viz.MainView.setPosition(0,5.5, -22)
	c1 = CTreadmillForcePlate()
#	
#	balls = []
#	for i in range(c1.numChannels):
#		b = viz.addTexQuad(pos=(0,i,1), color=viz.GRAY)
#		viz.addText3D(str(i), parent=b, scale=(0.5,0.5, 1), pos=(0,0,-0.1))
#		balls.append(b)
#	
#	def test1():
#		while True:
#			qq = c1.latestAinValues + c1.zero
#			for i in range(c1.numChannels):
#				balls[i].setPosition(qq[i],i,1)
#			yield None
#	viztask.schedule(test1)
#	
#	leftFoot = viz.add('white_ball.wrl', color=viz.GREEN)
#	rightFoot = viz.add('white_ball.wrl', color=viz.RED)
#	def test2():
#		while True:
#			left = c1.latestLeftCOP
#			leftFoot.setPosition(left[0], left[1]+5.5, -17)
#			right = c1.latestRightCOP
#			rightFoot.setPosition(right[0], right[1]+5.5, -17)
#			#for i in range(c1.numChannels):
#			#	balls[i].setPosition(100,i,1)
#			yield None
#	viztask.schedule(test2)
#	
#	import vizact
#	def leftoff():
#		leftFoot.alpha(0)
#	def lefton():
#		leftFoot.alpha(1)
#	def rightoff():
#		rightFoot.alpha(0)
#	def righton():
#		rightFoot.alpha(1)
#	viz.callback(LEFT_OFF_TREADMILL, leftoff)
#	viz.callback(LEFT_ON_TREADMILL, lefton)
#	viz.callback(RIGHT_OFF_TREADMILL, rightoff)
#	viz.callback(RIGHT_ON_TREADMILL, righton)
#	
#socket = socket(AF_INET, SOCK_STREAM)
#socket.connect(('128.174.14.105', 8089))		
#		
#def MyTask():
#    while True:
#        yield viztask.waitKeyDown('l')
#        char = b''
#        data = b''
#        while char !=b'}':
#           char = socket.recv(1)
#           data = data + char
#        msg = json.loads(data.decode('utf-8'))
#        if msg['stream'] == 8:
#            print(str(viz.tick()-1.963) + ',' + str(msg['value']))
#
#t = viztask.schedule( MyTask() )
#vizact.onkeydown('k',t.kill)

#def inertia(): 
#    while True: 
#        #yield viztask.waitTime( 0.5) 
#        #prev = tracker.getEuler() 
#        #viz.update(viz.UPDATE_PLUGINS) 
#        #if (tracker.getEuler() != prev):
##yield viztask.waitTime( 0.1)
#		logfile1.write("\n")
#		yield viztask.waitTime( 0.1)
#		logfile1.write(str(self.latestAinValues[0]))
#		logfile1.write("    ")
#		logfile1.write(str(viz.tick()))
#myTask = viztask.schedule( inertia() ) 
#vizact.onkeydown( 'K', myTask.kill )
#
#logfile1 = open("testlabjack.txt", "w")
#logfile1.write("ana0    time")
#logfile1.flush()
#
#print str(self.latestAinValues[0])

#threshold = 2.5
#init_v = 0
#current_v = self.latestAinValues[1]
##self.latestAinValues[1]
#
#def detecttiming():
#	while True:
#		if self.latestAinValues[1]>init_v+threshold:
#			print "begintime detected"
#			init_v = 100
#			
#		end
#viztask.schedule(detecttiming() )
#		

###########################
###EEG 
###########################
parallel_port = 0xC050 #binary 1100000010100000 = 49232
	
import random
import sendPulse
S1 = sendPulse.SendPulse(parallel_port)
	
#time between eeg calibration pulses (approx) and 
#the spacing between the eeg timing codes
EEG_TIMING_DELAY_LOW 	= 1
EEG_TIMING_DELAY_HIGH 	= 10
EEG_SPACING 			= 0.1 #time interval
EEG_TIMING_MARK 		= 1
	
eegfile = 'eeglog.txt'
EEGlogger = open(eegfile, 'w')
# sends the current viztick to the eeg and the data file
# This is called from a separate thread
def MarkEEG():
	while True:
		#pause for a while
		viz.waittime(random.randint(EEG_TIMING_DELAY_LOW, EEG_TIMING_DELAY_HIGH))
		#send a sequence to the eeg to mark
		recordTime = S1.generateTimeCode()
		S1.sendPulse(EEG_TIMING_MARK)
		EEGlogger.write(str(recordTime)+"\n")
		EEGlogger.flush()
		#send the rest
		if S1.tickSplit != None:
			for sendValIter in S1.tickSplit:
				viz.waittime(EEG_SPACING)
				S1.sendPulse(sendValIter)
eegThread = viz.director( MarkEEG )

eegThread = viz.director( MarkEEG ) #executes as a seperate process





viz.go()
gallery = viz.addChild('gallery.ive')

#trial_time = 50 #Change the number of seconds your trials run for

logfile1 = open("swaybaseline.txt", "w")
logfile1.write("[Yaw, Pitch, Roll]    time")
logfile1.flush()



log = text_log.TextLog("")
import logutil
logger = logutil.TrialLogger()
#logger.addSimpleSensor(loadCell, 'load_cell', 1000)

logger.addSimpleSensor(log, 'notes', 1000)
