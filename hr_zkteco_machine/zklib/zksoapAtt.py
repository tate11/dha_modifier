from struct import pack, unpack
from datetime import datetime, date

from zkconst import *
import xml.etree.cElementTree as et
import requests
import datetime




def zksoapAtt(self):

	data = []
	url = "http://" + str(self.ip) + "/iWsService"
	headers = {'content-type': 'text/xml'}
	body = """ <GetAttLog><ArgComKey
	xsi:type=\"xsd:integer\">0</ArgComKey><Arg><PIN
	xsi:type=\"xsd:integer\">All</PIN></Arg></GetAttLog>"""
	response = requests.post(url,data=body,headers=headers)
	#print response.text
	temp = response.text

	if temp:
		tree = et.fromstring(temp)
		container = tree.findall("Row")

		for elem in container:

			uid = elem.findtext("PIN")
			DateTime = elem.findtext("DateTime")
			ver = elem.findtext("Verified")
			state = elem.findtext("Status")
			workCode = elem.findtext("WorkCode")
			data.append((int(uid),datetime.datetime.strptime(str(DateTime),'%Y-%m-%d %H:%M:%S'),int(ver),int(state),int(workCode)))

		return data



	