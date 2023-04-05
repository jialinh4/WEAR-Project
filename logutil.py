#Modified by Joe Snider, 2/10
#
#Changed to accept simple sensors without built in python callbacks (for backward compatibility)
#  new simple sensors must have startRecording(int), stopRecording, and dumpRecording(filename) interface
#
#Previous types require the sensor to send the viz.SENSOR_RECORD_EVENT event.


import os
import viz
import itertools

def createNewTrialLogDirectory(base=''):
	"""Creates and returns the name of a new trial log directory.
	Diretory names will be 'trialXXX' where XXX is an incrementing number.
	base - Base directory to create trial directories in, defaults to current directory"""
	
	def _dirname(val):
		return os.path.join(base,'trial%03d' % (val))
	
	number = 1
	while os.path.exists(_dirname(number)):
		number += 1
	
	dir = _dirname(number)
	os.mkdir(dir)
	return dir

def logSensorData(filename,data,columns=None,header=True,splitFields=None,sep=' '):
	"""Log recorded sensor data to the specified filename
	filename - File to log data to
	data - 'data' field from sensor record event
	columns - List of data field names to record, defaults to all fields
	header - Write column header at beginning of file?
	splitFields - Dictionary that maps field name to list of subfields names, defaults to common fields (position,force,quat)
	sep - Character for separating data within log file, defaults to space"""
	
	#Make sure data array has at least one entry
	if not data:
		return
	
	#If splitFields is not specified, use common defaults (position,force,quat)
	if splitFields is None:
		splitFields = {}
		splitFields['position'] = ['x','y','z']
		splitFields['force'] = ['fx','fy','fz']
		splitFields['quat'] = ['qx','qy','qz','qw']
	
	#If columns is not specified then use all of them, but make sure 'time' field is first though
	if columns is None:
		columns = list(data[0].keys())
		if 'time' in columns:
			columns.remove('time')
			columns.insert(0,'time')
	
	#Open log file
	f = open(filename,'w')
	
	#Write header
	if header:
		names = []
		for field in columns:
			if field in splitFields:
				names.extend(splitFields[field])
			else:
				names.append(field)
		names.append('\n')
		f.write( sep.join(names) )
		
	#Write data
	for e in data:
		
		line = []
		
		for field in columns:
			if field in splitFields:
				line.extend( ( str(x) for x in e[field] ) )
			else:
				line.append(str(e[field]))
		
		line.append('\n')
		f.write( sep.join(line) )
		
	#Close log file
	f.close()

#Custom trial logger events
TRIAL_FINISHED_EVENT = viz.getEventID('logutil_TrialFinished')

class TrialLogger(viz.EventClass):
	"""Class for logging trials of recorded sensor data"""
	
	def __init__(self):
		
		#Initialize variables
		self._sensors = {}
		self._simpleSensors = {}
		self._trialRunning = False
		self._trialDirectory = ''
		
		#Initialize base class
		viz.EventClass.__init__(self)
		self.callback(viz.SENSOR_RECORD_EVENT,self._onSensorRecord)

	def checkRecordingDone(self):
		#Check if all sensors have finished recording and clear running flag
		for data in itertools.chain(self._sensors.itervalues(), self._simpleSensors.itervalues()):
			if not data.recorded:
				return
		self._trialRunning = False
			
		#Trigger trial finished event
		viz.sendEvent(TRIAL_FINISHED_EVENT,viz.Event(object=self))
		
	def _onSensorRecord(self,e):
		"""Triggered when sensor has finished recording"""
		if self._trialRunning and e.object in self._sensors:
			
			#Create log filename for sensor
			filename = os.path.join(self._trialDirectory,self._sensors[e.object].name+'.log')
			
			#Record data to file
			logSensorData(filename,e.data)
	
			#Set recorded flag
			self._sensors[e.object].recorded = True
			
			#check if there's anything else to do
			self.checkRecordingDone()
			
	#do direct dumping when no callback is easy to implement
	#requires the e.dumpRecording(filename) to exist
	def directRecord(self, e):
		if self._trialRunning and e in self._simpleSensors:
			
			#Create log filename for sensor
			filename = os.path.join(self._trialDirectory,self._simpleSensors[e].name+'.log')
			
			#Record data to file
			e.dumpRecording(filename)
	
			#Set recorded flag
			self._simpleSensors[e].recorded = True
			
			#check if there's anything else to do
			self.checkRecordingDone()
			
			
	def addSensor(self,object,name,samples):
		"""Add sensor object to logger"""
		self._sensors[object] = viz.Data(name=name,samples=samples,recorded=False)
		
	def addSimpleSensor(self,object,name,samples=-1):
		"""Add sensor object to logger"""
		self._simpleSensors[object] = viz.Data(name=name,samples=samples,recorded=False)
		
	def isTrialRunning(self):
		"""Return whether a trial is running"""
		return self._trialRunning
	
	def getTrialDirectory(self):
		"""Get directory for current trial log files"""
		return self._trialDirectory
	
	def startTrial(self):
		
		#Stop existing trial and don't record data
		self.stopTrial(False)
		
		#Create directory for logging trial data
		self._trialDirectory = createNewTrialLogDirectory()
		
		#Start recording sensor data
		for sensor,data in itertools.chain(self._sensors.iteritems(), self._simpleSensors.iteritems()):
			data.recorded = False
			sensor.startRecording(data.samples)
			#if not sensor.startRecording(data.samples):
			#	viz.logError('Failed to start recording')
		
		#Set running flag
		self._trialRunning = True
		
	def stopTrial(self,recordData=True):
		"""Stop recording data for this trial"""
		
		#Stop recording data
		for sensor,data in self._sensors.iteritems():
			sensor.stopRecording(recordData)
			
		for sensor,data in self._simpleSensors.iteritems():
			sensor.stopRecording()
			self.directRecord(sensor)
		
		#Clear running flag
		self._trialRunning = False
		
if __name__ == '__main__':
	
	viz.go()
	print "adsf"
