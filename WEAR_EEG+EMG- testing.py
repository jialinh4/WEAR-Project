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

logfile10 = open("testlabjack.txt", "w")
logfile10.write("begintime           endtime")
logfile10.flush()


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
			msg1.message("%6.3f %6.3f %6.3f %6.3f"%(self.latestAinValues[4], self.latestAinValues[5], self.latestAinValues[6], self.latestAinValues[7]))
			msg2.message("%6.3f %6.3f %6.3f %6.3f"%(self.latestAinValues[0], self.latestAinValues[1], self.latestAinValues[2], self.latestAinValues[3]))
			def inertia(): 
				while True: 

					logfile12.write("\n")
					yield viztask.waitTime( 0.1)

					logfile12.write(str(self.latestAinValues[1]))
					logfile12.write("    ")

					logfile12.write(str(viz.tick()))
			myTask = viztask.schedule( inertia() ) 
			vizact.onkeydown( 'K', myTask.kill )




			log1 = text_log.TextLog("")
			import logutil
			logger = logutil.TrialLogger()
			logger.addSimpleSensor(log1, 'note1', 1)

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

	c1 = CTreadmillForcePlate()

###########################
###EEG 
###########################
parallel_port = 0xC050
	
import random
import sendPulse
S1 = sendPulse.SendPulse(parallel_port)
	
#time between eeg calibration pulses (approx) and 
#the spacing between the eeg timing codes
EEG_TIMING_DELAY_LOW 	= 1
EEG_TIMING_DELAY_HIGH 	= 10
EEG_SPACING 			= 0.1
EEG_TIMING_MARK 		= 1
	
eegfile = 'swaybaseline_eeglog.txt'
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

######################
#####task
######################



viz.go()
gallery = viz.addChild('gallery.ive')
isense = viz.add('intersense.dle')
tracker = isense.addTracker(port=22, station=1) #Change port number to correct Com

logfile1 = open("swaybaseline.txt", "w")
logfile1.write("[Yaw, Pitch, Roll]    time")
logfile1.flush()


log = text_log.TextLog("")
import logutil
logger = logutil.TrialLogger()

logger.addSimpleSensor(log, 'notes', 1000)

