from struct import pack, unpack
from datetime import datetime, date
import sys

from zkconst import *



def acmOK(self):
	"""send CMD_ACK_OK"""
	""" try cmd_ack_data"""
	command = CMD_ACK_DATA
	command_string = ''
	chksum = 0
	session_id = 0
	reply_id = -1 + USHRT_MAX

	buf = self.createHeader(command, chksum, session_id,
		reply_id, command_string)
	
	self.zkclient.sendto(buf, self.address)
	
	try:
		self.data_recv, addr = self.zkclient.recvfrom(1024)
		self.session_id = unpack('HHHH', self.data_recv[:8])[2]
		
		return self.checkValid( self.data_recv )
	except:
		return False



def reverseHex(hexstr):
	tmp = ''
	for i in reversed( xrange( len(hexstr)/2 ) ):
		tmp += hexstr[i*2:(i*2)+2]
	
	return tmp

	#assume a socket disconnect (data returned is empty string) means  all data was #done being sent.
def recv_basic(the_socket):
    total_data=[]
    while True:
        data = the_socket.recv(8192)
        if not data: break
        total_data.append(data)
    return ''.join(total_data)
    
def recv_timeout(the_socket,timeout=2):
    the_socket.setblocking(0)
    total_data=[];data='';begin=time.time()
    while 1:
        #if you got some data, then break after wait sec
        if total_data and time.time()-begin>timeout:
            break
        #if you got no data at all, wait a little longer
        elif time.time()-begin>timeout*2:
            break
        try:
            data=the_socket.recv(8192)
            if data:
                total_data.append(data)
                begin=time.time()
            else:
                time.sleep(0.1)
        except:
            pass
    return ''.join(total_data)

End= 2000
def recv_end(the_socket):
    total_data=[];data=''
    while True:
            data=the_socket.recv(8192)
            if End in data:
                total_data.append(data[:data.find(End)])
                break
            total_data.append(data)
            if len(total_data)>1:
                #check if end_of_data was split
                last_pair=total_data[-2]+total_data[-1]
                if End in last_pair:
                    total_data[-2]=last_pair[:last_pair.find(End)]
                    total_data.pop()
                    break
    return ''.join(total_data)

def recv_size(the_socket):
    #data length is packed into 4 bytes
    total_len=0;total_data=[];size=sys.maxint
    size_data=sock_data='';recv_size=8192
    while total_len<size:
        sock_data=the_socket.recv(recv_size)
        if not total_data:
            if len(sock_data)>4:
                size_data+=sock_data
                size=struct.unpack('>i', size_data[:4])[0]
                recv_size=size
                if recv_size>524288:recv_size=524288
                total_data.append(size_data[4:])
            else:
                size_data+=sock_data
        else:
            total_data.append(sock_data)
        total_len=sum([len(i) for i in total_data ])
    return ''.join(total_data)




def zkAtt(self):



	atti = []
	i = 0
	command = CMD_ATTLOG_RRQ
	comand_string = ''
	chksum = 0
	session_id = self.session_id
	reply_id = unpack('4H',self.data_recv[:8])[3]

	buf = self.createHeader(command,chksum,session_id, reply_id, comand_string)

	for x in xrange(10):

		self.zkclient.sendto(buf,self.address)


   
	size = None
	attendance = []  
	data_recv, addr = self.zkclient.recvfrom(3094)

	#print "size", sys.getsizeof(data_recv)
	#print "size", len(data_recv)
	lensi = len(data_recv) / 2
	fstri = str(lensi) + "H"
	#print "first unpack   ", unpack (fstri, data_recv)


	if unpack('4H',data_recv[:8])[0] == CMD_PREPARE_DATA:
		#print "received CMD_PREPARE_DATA"
		size = unpack('I', data_recv[8:12])[0]
		
		
		
		#print 'Receiving %s %s' % (size,"bytes")
		#data_recv, addr = self.zkclient.recvfrom(43773)
		#lens = len(self.data_recv) / 2
		#fstr = str(lens) + "H"	
		#print "second unpack", unpack(fstr, self.data_recv)



		
		

		while unpack('4H', data_recv[:8])[0] != CMD_ACK_OK or unpack('4H', data_recv[:8])[0] == CMD_DATA:


			#print "COUNTER", i

			data_recv, addr = self.zkclient.recvfrom(size)

			lens = len(data_recv[:8]) / 2
			fstr = str(lens) + "H"
			if unpack(fstr, data_recv[:8])[0] == CMD_DATA:
				i = i +1
				#print "data package " , unpack(fstr, data_recv[:8])[0]
				lens = len(data_recv) / 2
				fstr = str(lens) + "H"

				#print "data unpack", unpack(fstr, data_recv)
				if i == 1:


					self.attendancedata.append(data_recv)
				elif i == 2:
					#atti.append(data_recv)
					self.attendancedata.append(data_recv)


			
			
				#acmOK(self)
		if unpack('4H', data_recv[:8])[0] == CMD_ACK_OK:
			print "CMD_ACK_OK"
				
		
			

		print "length of att data", len(self.attendancedata)
		print "length of atti data", len(self.attendancedata)
		#data_recv = self.zkclient.recvfrom(8)

		for x in xrange(len(self.attendancedata)):


						#print self.attendancedata[x][8:]
						#self.attendancedata[x] = self.attendancedata[x][8:]
						#print self.attendancedata[x][0:]
			self.attendancedata[x] = self.attendancedata[x][0:]
			


		#atti = atti

		attendancedata = ''.join(self.attendancedata)
			
		attendancedata = attendancedata[14:]
		#attendancedata = attendancedata[14:]

		#test = getData(self)

		print "len attendancedata", len(attendancedata)
					
		while len(attendancedata):


			#print "att loop"




						
		
			if len(attendancedata[29:30]) == 1:

				pls = unpack('c',attendancedata[29:30])#[3]
			
						
			#statev = unpack('=2c',attendancedata[21:23])
			#datem = unpack('ii',attendancedata[:8])[1]
						


			uid, state, timestamp, space = unpack( '24s1s4s11s', attendancedata.ljust(40)[:40] )
			#ord(pls[0])

			#print "%s, %s, %s, %s" % (uid, ord(pls[0]), ord(space[0]), decode_time( int( reverseHex( timestamp.encode('hex') ), 16 ) ) )
			#print "%s, %s, %s, %s" % (uid, ord(pls[0]), ord(space[0]), decode_time( int( reverseHex( timestamp.encode('hex') ), 16 ) ) )
						#print "%s, %s, %s, %s" % (uid, state, space, timestamp)
			attendance.append( ( uid, ord(pls[0]), decode_time( int( reverseHex( timestamp.encode('hex') ), 16 ) ) ) )
			#test.append( ( uid, 1 , decode_time( int( reverseHex( timestamp.encode('hex') ), 16 ) ) ) )
			attendancedata = attendancedata[40:]
			#print "len attendancedata", len(attendancedata)
						
		return attendance







def zkclearattendance(self):
	"""Start a connection with the time clock"""
	command = CMD_CLEAR_ATTLOG
	command_string = ''
	chksum = 0
	session_id = self.session_id
	reply_id = unpack('HHHH', self.data_recv[:8])[3]

	buf = self.createHeader(command, chksum, session_id,
		reply_id, command_string)
	self.zkclient.sendto(buf, self.address)
	#print buf.encode("hex")
	try:
		self.data_recv, addr = self.zkclient.recvfrom(1024)
		self.session_id = unpack('HHHH', self.data_recv[:8])[2]
		return self.data_recv[8:]
	except:
		return False