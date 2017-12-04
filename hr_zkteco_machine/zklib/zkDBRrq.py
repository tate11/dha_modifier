from struct import pack, unpack
from datetime import datetime, date
import sys
from zkconst import *

def reverseHex(hexstr):
    tmp = ''
    for i in reversed( xrange( len(hexstr)/2 ) ):
        tmp += hexstr[i*2:(i*2)+2]
    
    return tmp

def zkDBRrq(self):
	"""Tell device to send us all attlog data"""
	attendance = []
	command = CMD_DB_RRQ	
	command_string = '\x01'
	chksum = 0
	session_id = self.session_id

	reply_id = unpack('HHHH', self.data_recv[:8])[3]

	buf = self.createHeader(command,chksum, session_id,reply_id, command_string)
	self.zkclient.sendto(buf,self.address)

	
	self.data_recv, addr = self.zkclient.recvfrom(1024)

	print "dbrrq length", sys.getsizeof(self.data_recv)
		

	self.session_id = unpack('HHHH', self.data_recv[:8])[2]

	lensi = len(self.data_recv) / 2
	fstri = str(lensi) + "H"
	print "unpack all  ", unpack (fstri, self.data_recv)
		
	self.data_recv, addr = self.zkclient.recvfrom(56781)
		
	if unpack('HHHH', self.data_recv[:8])[0]  == CMD_DATA or unpack('HHHH', self.data_recv[:8])[0]  == CMD_PREPARE_DATA:

			
		print "received CMD_ACK_OK or CMD_PREPARE_DATA"
		size = unpack('I', self.data_recv[8:12])[0]
		print "size %s", size
		dat_recvm, addr = self.zkclient.recvfrom(43773)
		lensi = len(dat_recvm) / 2
		fstri = str(lensi) + "H"
		print "unpack all first  ", unpack (fstri, dat_recvm)

		self.attendancedata.append(dat_recvm)

		#print unpack('4H',dat_recvm[:8])

		dat_recvm, addr = self.zkclient.recvfrom(43773)

			

		lensi = len(dat_recvm) / 2
		fstri = str(lensi) + "H"
		print "unpack all second ", unpack (fstri, dat_recvm)
		print "len self.attendancedata", len(self.attendancedata)



		for x in xrange(len(self.attendancedata)):
		 	print "inda loop"



						#print self.attendancedata[x][8:]
						#self.attendancedata[x] = self.attendancedata[x][8:]
						#print self.attendancedata[x][0:]
			self.attendancedata[x] = self.attendancedata[x][0:]

		print "outta loop"

		attendancedata = self.attendancedata

		attendancedata = ''.join(self.attendancedata)

		attendancedata = attendancedata[0:]

		print "len attendancedata", len(attendancedata)

		while len(attendancedata):
			print "in finale loop"
			
			#pls = unpack('c',self.attendancedata[29:30])

			uid, state, timestamp, space = unpack('24s1s4s11s', attendancedata.ljust(40)[:40])
			print "%s, %s, %s, %s" % (uid, 1, ord(space[0]), decode_time(int(reverseHex(timestamp.encode('hex')), 16 )))
			attendancedata = attendancedata[40:]

		return attendance

			
"""
		print "outta loop"
		attendancedata = self.attendancedata

		attendancedata = ''.join( self.attendancedata)
            
		attendancedata = attendancedata[14:]




		print "len attendancedata", len(attendancedata)
            		
        while len(attendancedata):



        	print "in finale loop"
        	#pls = unpack('c',self.attendancedata[29:30])
        	uid, state, timestamp, space = unpack( '24s1s4s11s', attendancedata.ljust(40)[:40] )
        	print "%s, %s, %s, %s" % (uid, 1, ord(space[0]), decode_time( int( reverseHex( timestamp.encode('hex') ), 16 ) ) )
        	attendancedata = attendancedata[40:]

		"""		
		
	
		