from struct import pack, unpack
from datetime import datetime, date
import sys

from zkconst import *

def reverseHex(hexstr):
    tmp = ''
    for i in reversed( xrange( len(hexstr)/2 ) ):
        tmp += hexstr[i*2:(i*2)+2]
    
    return tmp
    

def zkRegevent(self):
    """register for live events"""
    print "reg event"
    command = CMD_REG_EVENT
    command_string = ''
    chksum = 0
    session_id = 0
    reply_id = unpack('HHHH', self.data_recv[:8])[3]

    buf = self.createHeader(command, chksum, session_id,reply_id, command_string)
    self.zkclient.sendto(buf, self.address)
    #print buf.encode("hex")
 
    self.data_recv, addr = self.zkclient.recvfrom(1024)
    self.session_id = unpack('HHHH', self.data_recv[:8])[2]


    print "size", sys.getsizeof(data_recv)
    print "size", len(data_recv)
    lensi = len(data_recv) / 2
    fstri = str(lensi) + "H"
    print "first unpack   ", unpack (fstri, data_recv)


    if unpack('4H',data_recv[:8])[0] == CMD_PREPARE_DATA:

        print "received CMD_PREPARE_DATA"
        size = unpack('I', data_recv[8:12])[0]

    if unpack('4H', data_recv[:8])[0] == CMD_ACK_OK:
        print "CMD_ACK_OK from regevent"
        
        
        
        print 'Receiving %s %s' % (size,"bytes")
        #data_recv, addr = self.zkclient.recvfrom(43773)
        #lens = len(self.data_recv) / 2
        #fstr = str(lens) + "H" 
        #print "second unpack", unpack(fstr, self.data_recv)



        
        

    while True: #unpack('4H', data_recv[:8])[0] != CMD_ACK_OK or unpack('4H', data_recv[:8])[0] == CMD_DATA:



        print "COUNTER", i

        data_recv, addr = self.zkclient.recvfrom(size)

        lens = len(data_recv[:8]) / 2
        fstr = str(lens) + "H"
        if unpack(fstr, data_recv[:8])[0] == CMD_DATA:

            i = i +1
            print "data package " , unpack(fstr, data_recv[:8])[0]
            lens = len(data_recv) / 2
            fstr = str(lens) + "H"

            print "data unpack", unpack(fstr, data_recv)
            if i == 1:



                self.attendancedata.append(data_recv)
            elif i == 2:
                        #atti.append(data_recv)
                self.attendancedata.append(data_recv)
            if unpack('4H', data_recv[:8])[0] == CMD_ACK_OK:
                print "CMD_ACK_OK"


            
            
                #acmOK(self)
        if unpack('4H', data_recv[:8])[0] == CMD_ACK_OK:
            print "CMD_ACK_OK"

 