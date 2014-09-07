import requests
from lxml import html
import time
import json
import fnmatch
from requests.exceptions import ConnectionError

tic = time.time()

try:
    response = requests.get('http://www.healthspace.com/Clients/Missouri/StLouis/St_Louis_Web_Live.nsf/Food-WardList?OpenView&Count=999&')
except ConnectionError:
	time.sleep(1)
	response = requests.get('http://www.healthspace.com/Clients/Missouri/StLouis/St_Louis_Web_Live.nsf/Food-WardList?OpenView&Count=999&')
parsed_body = html.fromstring(response.text)

ward_link = parsed_body.xpath('//a/@href')
ward_name = parsed_body.xpath('//a/text()')
ward_name[7] = 'append'

ward_list = {}
facility_link_start_list = {}
for i in range(len(ward_link)):
	s = 'http://www.healthspace.com' + ward_link[i]
	try:
		response = requests.get(s)
	except ConnectionError:
		time.sleep(1)
		response = requests.get(s)
	parsed_body = html.fromstring(response.text)
	facility_link_start_list[0] = parsed_body.xpath('//a/@href')

	if 'start=' in facility_link_start_list[0][-1]:
		start = facility_link_start_list[0][-1]
		del facility_link_start_list[0][-1]
		s = 'http://www.healthspace.com/Clients/Missouri/StLouis/St_Louis_Web_Live.nsf/' + start
		try:
			response = requests.get(s)
		except ConnectionError:
			time.sleep(1)
			response = requests.get(s)
		parsed_body = html.fromstring(response.text)
		facility_link_start_list[1] = parsed_body.xpath('//a/@href')
		
		n = 1
		while 'start=' in facility_link_start_list[n][-2]:
			start = facility_link_start_list[n][-1]
			del facility_link_start_list[n][-1]
			del facility_link_start_list[n][-1]
			s = 'http://www.healthspace.com/Clients/Missouri/StLouis/St_Louis_Web_Live.nsf/' + start
			try:
				response = requests.get(s)
			except ConnectionError:
				time.sleep(1)
				response = requests.get(s)
			parsed_body = html.fromstring(response.text)
			n = n + 1
			facility_link_start_list[n] = parsed_body.xpath('//a/@href')

		del facility_link_start_list[n][-1]
	
	facility_link = []
	for n in range(len(facility_link_start_list)):
		facility_link = facility_link + facility_link_start_list[n]
		
	facility_list = {}
	for j in range(len(facility_link)):
		s = 'http://www.healthspace.com' + facility_link[j]
		try:	
			response = requests.get(s)
		except ConnectionError:
			time.sleep(1)
			response = requests.get(s)
		parsed_body = html.fromstring(response.text)

		facility_name = parsed_body.xpath('//h2/text()')
		facility_name = facility_name[0]
		facility_location = parsed_body.xpath('//p/text()') 
		facility_location = facility_location[1].strip('\n')
		
		facility_information = parsed_body.xpath('//td/text()')
		
		facility_type = facility_information[1]
		facility_phone = facility_information[3]
		facility_smoking = facility_information[5]

		facility_inspection_link = parsed_body.xpath('//a/@href')
		del facility_inspection_link[0:2]

		inspection_list = {}
		for k in range(len(facility_inspection_link)):
			s = 'http://www.healthspace.com/Clients/Missouri/StLouis/St_Louis_Web_Live.nsf/' + facility_inspection_link[k]
			try:
				response = requests.get(s)
			except ConnectionError:
				time.sleep(1)
				response = requests.get(s)
			parsed_body = html.fromstring(response.text)
			inspection_information = parsed_body.xpath('//td/text()')
			tagged = parsed_body.xpath('//font/text()')

			for n in range(len(inspection_information)):
				inspection_information[n] = inspection_information[n].replace(u'\xa0', '').encode('utf-8')
				inspection_information[n] = inspection_information[n].strip()

			for n in range(len(tagged)):
				tagged[n] = tagged[n].replace(u'\xa0', '').encode('utf-8')
				tagged[n] = tagged[n].strip()

			dict = {}    
			filtered = fnmatch.filter(inspection_information, '*:')
			for n in range(len(filtered)):
				q = inspection_information.index(filtered[n])     
				if inspection_information[q+1] in filtered:
					inspection_information[q] = inspection_information[q].strip(':')
					dict[inspection_information[q]] = ''      
				else:
					inspection_information[q] = inspection_information[q].strip(':')
					dict[inspection_information[q]] = inspection_information[q+1]

			filtered = fnmatch.filter(inspection_information, '?-???.?? / *')      
			for n in range(len(filtered)):
				q = inspection_information.index(filtered[n])
				dict[inspection_information[q]] = {'Comments' : inspection_information[q+1], 'Tag' : tagged[n]}

			inspection_list[dict['Inspection date']] = dict   
            
		facility_list[facility_name] = {'Facility Name' : facility_name, 'Facility Location' : facility_location, 'Facility Type' : facility_type, 'Phone Number' : facility_phone, 'Smoking Status' : facility_smoking, 'Inspection History' : inspection_list}

	ward_list['Ward ' + ward_name[i]] = facility_list
ward_list['Ward 7'].update(ward_list['Ward append'])
del ward_list['Ward append']
json.dump(ward_list, open("inspections.json", 'w'))

toc = time.time()
print toc-tic
