#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

@author: askahlon

"""




import datetime
import os

def convertTime(time): # takes a string of time as input and converts it into a time obj
	dateObj = datetime.datetime.strptime(time, '%Y.%j.%H:%M:%S') #%j represents zero padded day of year
	return dateObj 

def convertTime2(time): # takes a string of time as input and converts it into a time obj
    dateObj = datetime.datetime.strptime(time, '%j.%H:%M:%S') #%j represents zero padded day of year
    return dateObj

def fetchlog(station, experiment):   # Dowlnloads the logfiles 
        if station == 'ho':  # 26m log lives on oper@hobart, not pcfsho
                print('Retrieving %s%s.log from oper@hobart' %(experiment,station))
                os.system('scp oper@hobart:/usr2/log/%s%s.log /vlbobs/ivs/logs/' %(experiment,station))
        else:     # hb, ke and yg have the same formats
                print('Retrieving %s%s.log from pcfs%s' %(experiment,station,station))
                os.system('scp oper@pcfs%s:/usr2/log/%s%s.log /vlbobs/ivs/logs/' %(station,experiment,station))

def openFile(logFilePath, station, experiment): # open email file to see if it is okay
		fileName = logFilePath+experiment+station+'.comments'
		os.system('emacs ' +fileName)

def findDoy(logFilePath): # reads the log file, return the day of year and year
	dayStart = 5 # index number of doy
	dayEnd = 8
	try:
		logfile= open(logFilePath,'r') # Read the log file
	except IOError:
		print "Cannot open "+ logFilePath
	for counter,line in enumerate(logfile): 
   # for each line
	    	if counter<1:
			doy = int(line[dayStart:dayEnd])
			year  = int(line[0:dayStart-1])
	logfile.close()
	return doy, year

def expStartStop(sumFilePath,doyRange,year): #finds the exp start and end times.
	dataStart = 19 # line number in the sum file where scan data starts
	scanStartIndexStart = 39
	scanStartIndexEnd =47
	scanEndIndexStart = 49
	scanEndIndexEnd =57
	try:
		sumFile = open(sumFilePath,'r')
	except IOError:
		print "Cannot open " + sumFilePath
	for count, line in enumerate(sumFile):
		if count >dataStart-1: # start on the 19th line
			if line[1:4] in doyRange: #check if line starts with doy
				if count == dataStart: #the 19th line has the first scan start time which is the exp start	
					scanStart = str(year)+'.'+line[1:4]+'.'+line[scanStartIndexStart:scanStartIndexEnd]
					scanStart = convertTime(scanStart)
				scanEnd = str(year)+'.'+line[1:4]+'.'+line[scanEndIndexStart:scanEndIndexEnd] #read all end times
				scanEnd = convertTime(scanEnd) #store the last end time
	sumFile.close()	
	return scanStart, scanEnd
def dataRecorded (logFilePath, doyRange, scanStart, scanEnd): #goes through the log file to work out module names and data recored 
	yearStart=0
	doystart = 5 # index of the string where time starts (from 0) 5 if including day
	doyEnd = 8
	timeStarts = 9   
	timeEnd = 17
	banks={} # dictionary containing the name and the data recorded
	diskPos = float(0)
	diskPosCount = 0
	offset = 0.0
	currentTime = None
	activeBank = None
	prevBank = None
	prevDisk = 0.0
	prevDiskPosCount = 0
	
	try:
		logfile= open(logFilePath,'r') # Read the log file
	except IOError:
		print "Cannot open "+ logFilePath
	for counter,line in enumerate(logfile):    # for each line
	    	currentTime = convertTime(line[yearStart:timeEnd]) #store the current time of the line in the log
		if currentTime >= scanStart and currentTime <= scanEnd+datetime.timedelta(0,60):
			if line[21:35] == 'mk5/!bank_set?' and line[36:37] == '0':
				#print line
				activeBank = line.split('/')[2].split(':')[2] # save the active bank
				#print 'Active',activeBank, '     Prev', prevBank
			if activeBank != prevBank and prevBank != None: #if the active bank has changed
				banks[prevBank] = diskPos - offset  # store the data recorded
				diskPosCount = 0   #set this count to zero to reset
			if line[21:30] == 'disk_pos/':
				diskPos= float(line.split('/')[-1].split(',')[0]) # save the disk position
				#print 'Read ', diskPos
				if diskPos < prevDiskPos and diskPosCount>1: # if the disk pos goes back before change taking effect
					#print 't1'
					diskPos = prevDiskPos
				
				#print 'disk pos is ' , diskPos
				diskPosCount = diskPosCount+1 # increment counter, becuase 1 means it will be used for offset
				if diskPosCount == 1:
					offset = diskPos # first time you read diskpos for new bank is offset
					#print 'ofset is ', offset
			prevBank = activeBank # initialise prevbank variable
			prevDiskPos = diskPos
			prevDiskPosCount = diskPosCount
			
	#print 'final disk pos is ' , diskPos
	banks[activeBank]= diskPos -offset
					
	logfile.close() # close I/O stream to free up resources
	return banks #output the array of times and the day of the year


def findErrors(logFilePath):   # reads the log files return the stow times and the day of the year
	########## Lets declare some index locations specific to the log file###########
	dayStart = 5
	dayEnd = 8
	timestart = 5    # index of the string where time starts (from 0) 5 if including day
	timeend = 16
	stowTimes = []   #array to store stow engage and release times
	#slewTimes = []
	stowed = False   # antenna is not stowed by default
	try:
		logfile= open(logFilePath,'r') # Read the log file
	except IOError:
		print "Cannot open "+ logFilePath
	for counter,line in enumerate(logfile):    # for each line
	    	if line[35:45] == '7mautostow': #look for mention of 7mautostow
			stowTimes.append(line[timestart:timeend +1])  #if you find it, save the time
			stowed = True
	    	if line[-19:-1] == 'Auto-stow released':  # also check for stow release
			stowTimes.append(line[timestart:timeend +1])  # save that time too 
			stowed = False
		#if line[30:37] == 'SLEWING': #look for mention of slewing errors
			#slewTimes.append(line[timestart:timeend +1])  #if you find it, save the time
	if stowed == True:
		stowTimes.append(line[timestart:timeend +1])
	endTime = line[timestart:timeend +1]
	logfile.close() # close I/O stream to free up resources
	return stowTimes #,slewTimes, doy output the array of times and the day of the year

def findScansAffected (sumFilePath,stowTimes,doyRange,telescopeSlew): # reads sumfile to workout the scans affected by windstows
	dataStart = 19 # line number in the sum file where scan data starts
	scanStartIndexStart = 39
	scanStartIndexEnd =47
	scanEndIndexStart = 49
	scanEndIndexEnd =57
	slewTime = telescopeSlew  # time it takes the telescope to move in seconds
	scansAffected = []
	prevScanEnd = None
	try:
		sumFile = open(sumFilePath,'r')
	except IOError:
		print "Cannot open " + sumFilePath
	for count, line in enumerate(sumFile):
		if count >dataStart-1:
			if line[1:4] in doyRange : #check if line starts with doy
				scanName = line[1:9]
				scanDoy = line[1:4]
				scanStart = line[1:4]+'.'+line[scanStartIndexStart:scanStartIndexEnd]
				scanEnd = line[1:4]+'.'+line[scanEndIndexStart:scanEndIndexEnd]
				scanStart = convertTime2(scanStart) - datetime.timedelta(0,slewTime)
				scanEnd = convertTime2(scanEnd) + datetime.timedelta(0,slewTime)
		   		for time in stowTimes:
		        		formattedTime = convertTime2(time) # convert stow time to a datetime obj
					if scanDoy == formattedTime.strftime('%j'):
			   			if formattedTime.time() >= scanStart.time() and formattedTime.time() <= scanEnd.time():
				   			scansAffected.append(line[1:9]) #store the scan name
						if prevScanEnd != None:
							if formattedTime.time() >= prevScanEnd.time() and formattedTime.time() <= scanStart.time():
								scansAffected.append(line[1:9]) #store the scan name
							
				prevScanEnd = scanEnd
	if len(scansAffected)<len(stowTimes): #if the sizes do not match
		scansAffected.append(scanName) # save the last scan name
	
	sumFile.close()
	return scansAffected

def formatWindData (stowTimes, scansAffectedStow): #format the windstow data to write it out nicely
	count=0
	count2=0
	temp =''
	stowTimesFormated = []
	scansAffectedFormated = []

	#print 'The windstow times for ' + experiment + station + ' are:\n'
	if len(stowTimes) != 0:
		while int(count/2) < int((len(stowTimes)/2)):    
			temp = stowTimes[count] + ' to ' + stowTimes[count+1] #writes the times in a x to y format
			count = count +2  
			stowTimesFormated.append(temp)

	
	if len(scansAffectedStow)!=0:
		while int(count2/2) < int((len(scansAffectedStow)/2)):    
			temp2= scansAffectedStow[count2] + ' to ' + scansAffectedStow[count2+1] 
			count2 = count2 +2  
			scansAffectedFormated.append(temp2) 

	return stowTimesFormated, scansAffectedFormated

def commasAnd(array): # puts the commas & "and" appropriately
	variable = ''
	lenght = len(array)
	if lenght == 1:
		return str(array[0])
	elif lenght == 2:
		return str(array[0])+ ' and ' +str(array[1])
	elif lenght > 2:
		for i in range(len(array)-1):
			variable = variable+str(array[i]) + ', '
		variable = variable + 'and ' + str(array[-1])
		return variable
	else:
		return 'empty'

def additionalComments (logFilePath, scanStart, scanEnd): #read all the comments made by observer so we can print them
	yearStart=0
	doystart = 5 # index of the string where time starts (from 0) 5 if including day
	doyEnd = 8
	timeStarts = 9   
	timeEnd = 17
	checkListComments = [] 
	tempComments = ''
	tempList = []
	#additionalNotes = 60:77 # index location of the phrase additional notes
	try:
		logfile= open(logFilePath,'r') # Read the log file
	except IOError:
		print "Cannot open "+ logFilePath
	for counter,line in enumerate(logfile):
		currentTime = convertTime(line[yearStart:timeEnd]) #store the current time of the line in the log
		if currentTime >= scanStart and currentTime <= scanEnd+datetime.timedelta(0,60): # if within the exp times
			if line [23:36] == 'Comment from'  and line [46:55] != 'CHECKLIST': #this avoids the checklists items 
				tempComments = str(currentTime.time())+' UT  ' +line[43:len(line)] 
				print 'a', tempComments
				checkListComments.append(tempComments)
			if line[60:77] == 'Additional notes:':
				if ':' in line [78:85] and 'UT' in line [78:85]:  # see if time is already included
					tempComments = line[78: len(line)]
					checkListComments.append(tempComments)
				else:
					if len(line[78: len(line)]) != 0:
						tempComments = str(currentTime.time())+' UT  ' + line[78:len(line)]
						checkListComments.append(tempComments)
	return checkListComments




def formatRecData(modules): #formatd the data with filler words
	tempStorage = [] 
	for keys, values in modules.iteritems():
		tempVariable = str("{0:.2f}".format(float(modules[keys])/float(1E+9))) + ' GB on '+ keys # stores as e.g. 3983.96 Gb in  HOB+1003
	   	tempStorage.append(tempVariable)
	return tempStorage

def writeEmail(logFilePath, modulesFormated, knownProblems,modeTransport, correlator, missedScans, observers, yourName, exp, station, logComments,stowFormated, scansFormated): #write it all
    
	fileName= logFilePath+exp+station+'.comments'
	f = open(fileName, 'w')
	f.write('Recorded ' +  commasAnd(modulesFormated)+ '.' + ' The module is being '+ modeTransport+ ' to ' + correlator +'.'+'\n' )
	f.write('\n' )
	f.write('\n' )
	f.write('Known Problems?'+'\n' )
	if len(stowFormated) != 0: # check if the stow times array is empty  
		if len(stowFormated) == 1:
			stowTemp = 'There was ' + str(len(stowFormated)) + ' windstow.'
		else:			
			stowTemp = 'There were ' + str(len(stowFormated))+ ' windstows.'

		f.write(knownProblems + ' ' +stowTemp+' '+'The windstow times are tabulated at the end of the email.\n') 	

	else:
		f.write(knownProblems+'\n' )
	f.write('\n' )
	f.write('\n' )
	f.write('Missed Scans?'+'\n' )
	if len(scansFormated) != 0:
		f.write(missedScans +' '+'The scans missed due to  windstow(s) were: \n ') 
		for items in scansFormated:
			f.write(items+'\n' )
	else :
		f.write(missedScans+'\n' )
	f.write('\n' )
	f.write('\n' )
	f.write('Observers'+'\n' )
	f.write(observers+'\n' )
	f.write('\n' )
	f.write('\n' )
	f.write('\n' )
	f.write('Regards,'+'\n' )
	f.write(yourName+'\n' )
	f.write('\n' )
	f.write('\n' )
	f.write('Comments from the Log:'+'\n')
	for line in logComments:
		f.write(line)
	f.write('\n' )
	f.write('Windstow times:'+'\n')
	if len(stowFormated) == 0:
		f.write('There were no windstows.\n')
	else:
		for item in stowFormated:
			f.write(item+'\n') 
	
def writeEmailHo(logFilePath, modulesFormated, knownProblems,modeTransport, correlator, missedScans, observers, yourName, exp, station, logComments):
	fileName = logFilePath+ exp+station+'.comments'
	f = open(fileName, 'w')
	f.write('Recorded ' +  commasAnd(modulesFormated)+ '.' + ' The module is being '+ modeTransport+ ' to ' + correlator +'.'+'\n' )
	f.write('\n' )
	f.write('\n' )
	f.write('Known Problems?'+'\n' )
	f.write(knownProblems+'\n' )

	f.write('\n' )
	f.write('\n' )
	f.write('Missed Scans?'+'\n' )
	f.write(missedScans+'\n' )
	f.write('\n' )
	f.write('\n' )
	f.write('Observers'+'\n' )

	f.write(observers+'\n' )
	f.write('\n' )
	f.write('\n' )
	f.write('\n' )
	f.write('Regards,'+'\n' )
	f.write(yourName+'\n' )
	f.write('\n' )
	f.write('\n' )
	f.write('Comments from the Log:'+'\n')
	for line in logComments:
		f.write(line)
		
def correctInput(question, correctValues):
	while True:
		usrInput = raw_input(question+'\n')
		if usrInput in correctValues:
			break
	return usrInput
	
		

def main():
	exp = raw_input('What is the name of the experiment? e.g. r1778 \n')
	station = correctInput('Which station? [hb|ke|yg|ho]', ['hb','ke','yg','ho'])
        #newLog = correctInput('Do you want to download the logfile? [y/n]', ['y','n'])
        #if newLog == 'y':
        fetchlog(station, exp)
	logFilePath = '/vlbobs/ivs/logs/'+exp+station+'.log'
	sumFilePath = '/vlbobs/ivs/sched/'+exp+station+'.sum'
        
	doy,year = findDoy(logFilePath)
	if doy <100:
		doyRange = ['0'+str(doy), '0'+ str(doy+1)]
	else:
		doyRange = [str(doy), str(doy+1)]
	if station == 'ho':
                expStartTime = convertTime(raw_input('What is the experiment start time? e.g. 2017.018.17:30:00\n'))
                expEndTime = convertTime(raw_input('What is the experiment end time? e.g. 2017.019.17:30:00\n'))
        else:
                expStartTime, expEndTime = expStartStop(sumFilePath,doyRange,year)
                
	modules = dataRecorded(logFilePath,doyRange, expStartTime, expEndTime)
	modulesFormated = formatRecData(modules)
	correlator = raw_input("Where is the data being sent to?" '\n')
	modeTransport = correctInput('Is the data being transfered electronically or shipped? [e\s]', ['e','s'])
		
	if modeTransport == 'e':
		modeTransport = 'transfered electronically'
	elif modeTransport == 's':
		modeTransport = 'sent via DHL'
	knownProblems =raw_input("Were there any known problems?" '\n')
	missedScans = raw_input("Were there any missed scans?" '\n')
	observers = raw_input("Who were the observers?" '\n')
	yourName = raw_input("And your name?" '\n')
	logComments = additionalComments(logFilePath, expStartTime, expEndTime)
	telescopeSlew = 10  #slew time of the telescope, to give it some time to reach source
	if station == 'ho':
                writeEmailHo(logFilePath, modulesFormated, knownProblems, modeTransport, correlator, missedScans, observers, yourName, exp, station, logComments)
        else:
                stowTimes = findErrors(logFilePath)
		for time in stowTimes:
			formatedTime = convertTime(str(year)+'.'+time)
			if formatedTime <= expStartTime or formatedTime >= expEndTime:
				stowTimes.remove(time)
                scansAffectedStow = findScansAffected(sumFilePath, stowTimes, doyRange,telescopeSlew)
                stowFormated, scansFormated = formatWindData(stowTimes, scansAffectedStow )
                writeEmail(logFilePath, modulesFormated, knownProblems, modeTransport, correlator, missedScans, observers, yourName, exp, station, logComments, stowFormated, scansFormated)
	openFile(logFilePath,station,exp)
	print '\n'
	print 'Please run flogit_auscope.pl to send the end of experiment email and upload the log file(s).'		

main()
