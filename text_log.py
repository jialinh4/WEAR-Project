#Joe Snider
#2/12
#
#Mimic a simple sensor that can act as a log file

class TextLog:
	#can send in some initial data (e.g. a header)
	# be sure to put a newline on the initial if desired
	def __init__(self, initial=""):
		self.initial = initial
		self.dumpStr = ""
		
	#the trials thing is for compatability with the logger
	def startRecording(self, trials=0):
		self.clearRecording()
	def stopRecording(self, junk=0):
		pass
		
	#dump the recorded data to the file fileName
	def dumpRecording(self, fileName):
		fil = open(fileName, 'w')
		fil.write(self.initial)
		fil.write(self.dumpStr)
		self.dumpStr = ""
		
	def clearRecording(self):
		self.dumpStr = ""
		
	#add something to the log (newlines etc.. are your resp.)
	def Record(self, data):
		self.dumpStr += data

if __name__ == "__main__":
	import logutil
	
	Tl = TextLog("asdf sadf sewr\n")
	
	logger = logutil.TrialLogger()
	logger.addSimpleSensor(Tl, 'event_log', 100)
	
	logger.startTrial()
	Tl.Record("%g %d %d\n"%(1.123, 3, 5))
	Tl.Record("whatever I want")
	logger.stopTrial()
	