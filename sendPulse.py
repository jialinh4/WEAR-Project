import vizparallel
import viz
import vizact
import viztask
import struct

class SendPulse(viz.EventClass):
	#port is the port
	def __init__(self, port):
		self.port = port
		self.portOpen = True
		self.tick = 0.0
		self.tickSplit = None
		viz.EventClass.__init__(self)
		
	def __del__(self):
		self.stopPulse()
		
	#clear the port and flag it as writeable
	#called automatically after sendPulse
	def stopPulse(self):
		vizparallel.write(0, self.port)
		self.portOpen = True

	#Sends a pulse to the parallel port
	def sendPulse(self, n):
		if n < 1 or n > 255:
			#viz.logError("Warning: SendPulse.sendPulse attempted to send a bad value (%d) ... sending 1 instead"%(n))
			n = 1
		if self.portOpen:
			value = int(n)
			vizparallel.write(value, self.port)
			self.portOpen = False
			# in 1./60. = 0.16 milliseconds call the write function to clear the channels
			vizact.ontimer2(1./60., 0, self.stopPulse)
		else:
			#viz.logError("Warning: sendPulse.sendPulse unable to send for at least 1./60. seconds ... skipping")
			pass
			
	#generate the time code for the current Vizard tick
	#casts the time to a float (32 bits) and breaks it up into 4 8 bit ints
	#keeps trying until all ints are nonzero
	#returns the time when the viz.tick was grabbed or assigns tickSplit = [1,1,1,1] and self.tick=-1 on failure
	#    and return the current time (on failure)
	def generateTimeCode(self):
		self.tick = viz.tick()
		atLeastOneZero = 100
		while atLeastOneZero > 1:
			self.tick = viz.tick()
			longVal = struct.unpack('I', struct.pack('f', self.tick))[0]
			#self.tickSplit = [int(longVal&255), int((longVal>>8)&255), int((longVal>>16)&255), int((longVal>>24)&255)]
			self.tickSplit = [1+int(longVal&15),1+int((longVal>>4)&15),1+int((longVal>>8)&15),1+int((longVal>>12)&15),1+int((longVal>>16)&15),1+int((longVal>>20)&15),1+int((longVal>>24)&15),1+int((longVal>>28)&15)]
			temp = atLeastOneZero - 1
			atLeastOneZero = -1
			for i in self.tickSplit:
				if i == 0:
					viz.logError("Warning: skipped a viz tick (%g) when generating eeg time"%(self.tick))
					atLeastOneZero = temp
		if atLeastOneZero < 0:
			#success
			return self.tick
		else:
			#failure
			viz.logError("Warning: unable to generate an eeg time for %g"%(self.tick))
			self.tickSplit = [1,1,1,1]
			return self.tick
		#should not get here
		viz.logError("Error: bad time in sendPulse.generateTimeCode")
		return -1
					
	#send a timing pulse (viz.tick split into 4*8 bit integers)
	#spacing = the time (in seconds) between pulses (pause, pulse, pause, pulse, pause, pulse, pause, pulse)
	#call with a scheduler
	def sendTiming(self, spacing):
		if self.tickSplit != None:
			for sendValIter in self.tickSplit:
				yield viztask.waitTime(spacing)
				self.sendPulse(sendValIter)


if __name__ == '__main__':
	import viz
	import random
	viz.go()
	
	fileTest = open("file.txt", 'w')
	def Scheduled():
		S1 = SendPulse(0xC050)
		while True:
			#send an integer, e.g., trial
			yield viztask.waitTime(1)
			val = 255#random.randint(1,255)
			S1.sendPulse(val)
			print "sending ",val
			fileTest.write(str(viz.tick())+" "+str(val)+'\n')
			fileTest.flush()
#			#mark a time in a sendable format
#			testTime = S1.generateTimeCode()
#			print "Found time",testTime
#			S1.sendPulse(110)
#			yield viztask.waitTime(0.1)
#			#send an integer, e.g., block
#			S1.sendPulse(random.randint(1,255))
#				
#			#send an integer, e.g., trial
#			yield viztask.waitTime(0.1)
#			S1.sendPulse(random.randint(1,255))
#			
#			#send the timing code
#			#This must be yielded to to get proper results
#			#It will take 4*0.1 seconds to finish
#			yield S1.sendTiming(0.1)
#			yield viztask.waitTime(1.-0.6)
#			
#			#send more pulses
#			S1.sendPulse(120)
#			yield viztask.waitTime(1)
#			S1.sendPulse(130)
#			yield viztask.waitTime(1)
	viztask.schedule( Scheduled() )