#!/usr/bin/python
#KVH HTS-feed program
#Hayden S. Maclean -> hmaclean@kvh.com

from datetime import date, timedelta
import datetime
import requests
from pygelf import GelfUdpHandler
import logging
import subprocess
import os
import memcache
import pickle
import sys
import traceback
from pprint import pprint
def send_hb():
  hb_config = {}
  hb_config['origin'] = "HTS Terminal Stats Processor"
  hb_config['timeout'] = 300
  hb_config['tags'] = ["Mclean,Docker,dev_hts_bot"]
  r = requests.post("http://192.168.220.35:8080/api/heartbeat",json=hb_config,timeout=10)


s3bucket="s3://kvh-hts-statistics/"
element_list = ['beam','gsp','inet','sspc','terminal']
#element_list = ['beam','gsp','inet','terminal']

ds_modcod={0:'0.QPSK 1/4',
1:'1.QPSK 1/3',
2:'2.8PSK 1/4',
3:'3.QPSK 2/5',
4:'4.QPSK 1/2',
5:'5.8PSK 1/3',
6:'6.16APSK 1/4',
7:'7.QPSK 3/5',
8:'8.8PSK 2/5',
9:'9.32APSK 1/4',
10:'10.QPSK 2/3',
11:'11.16APSK 1/3',
12:'12.QPSK 3/4',
13:'13.8PSK 1/2',
14:'14.QPSK 4/5',
15:'15.16APSK 2/5',
16:'16.32APSK 1/3',
17:'17.QPSK 5/6',
18:'18.QPSK 8/9',
19:'19.8PSK 3/5',
20:'20.QPSK 9/10',
21:'21.8PSK 2/3',
22:'22.16APSK 1/2',
23:'23.32APSK 2/5',
24:'24.8PSK 3/4',
25:'25.16APSK 3/5',
26:'26.8PSK 4/5',
27:'27.8PSK 5/6',
28:'28.32APSK 1/2',
29:'29.8PSK 8/9',
30:'30.16APSK 2/3',
31:'31.8PSK 9/10',
32:'32.16APSK 3/4',
33:'33.32APSK 3/5',
34:'34.16APSK 4/5',
35:'35.32APSK 2/3',
36:'36.16APSK 5/6',
37:'37.16APSK 8/9',
38:'38.16APSK 9/10',
39:'39.32APSK 3/4',
40:'40.32APSK 4/5',
41:'41.32APSK 5/6',
42:'42.32APSK 8/9',
43:'43.32APSK 9/10'}


us_modcod={0:'0.BPSK 1/3 SF=16',
1:'1.BPSK 1/2 SF=16',
2:'2.BPSK 2/3 SF=16',
3:'3.BPSK 1/3 SF=8',
4:'4.BPSK 3/4 SF=16',
5:'5.BPSK 4/5 SF=16',
6:'6.BPSK 5/6 SF=16',
7:'7.BPSK 6/7 SF=16',
8:'8.BPSK 7/8 SF=16',
9:'9.BPSK 1/2 SF=8',
10:'10.BPSK 2/3 SF=8',
11:'11.BPSK 1/3 SF=4',
12:'12.BPSK 3/4 SF=8',
13:'13.BPSK 4/5 SF=8',
14:'14.BPSK 5/6 SF=8',
15:'15.BPSK 6/7 SF=8',
16:'16.BPSK 7/8 SF=8',
17:'17.BPSK 1/2 SF=4',
18:'18.BPSK 2/3 SF=4',
19:'19.BPSK 1/3 SF=2',
20:'20.BPSK 3/4 SF=4',
21:'21.BPSK 4/5 SF=4',
22:'22.BPSK 5/6 SF=4',
23:'23.BPSK 6/7 SF=4',
24:'24.BPSK 7/8 SF=4',
25:'25.BPSK 1/2 SF=2',
26:'26.BPSK 2/3 SF=2',
27:'27.BPSK 1/3',
28:'28.BPSK 3/4 SF=2',
29:'29.BPSK 4/5 SF=2',
30:'30.BPSK 5/6 SF=2',
31:'31.BPSK 6/7 SF=2',
32:'32.BPSK 7/8 SF=2',
33:'33.BPSK 1/2',
34:'34.BPSK 2/3',
35:'35.QPSK 1/3',
36:'36.BPSK 3/4',
37:'37.BPSK 4/5',
38:'38.BPSK 5/6',
39:'39.BPSK 6/7',
40:'40.BPSK 7/8',
41:'41.QPSK 1/2',
42:'42.8PSK 1/3',
43:'43.QPSK 2/3',
44:'44.16-ary 1/3',
45:'45.QPSK 3/4',
46:'46.8PSK 1/2',
47:'47.QPSK 4/5',
48:'48.QPSK 5/6',
49:'49.QPSK 6/7',
50:'50.QPSK 7/8',
51:'51.8PSK 2/3',
52:'52.16-ary 1/2',
53:'53.8PSK 3/4',
54:'54.8PSK 4/5',
55:'55.8PSK 5/6',
56:'56.8PSK 6/7',
57:'57.8PSK 7/8',
58:'58.16-ary 2/3',
59:'59.16-ary 3/4',
60:'60.16-ary 4/5',
61:'61.16-ary 5/6',
62:'62.16-ary 6/7',
63:'63.16-ary 7/8'}


# Logging
logging.basicConfig(filename='/root/hts-stats.log',format='%(asctime)s %(levelname)s %(message)s',level=logging.WARNING)

# logging.basicConfig(level=logging.CRITICAL)
# logger = logging.getLogger()
# logger.addHandler(GelfUdpHandler(host='graylog.ops.kvh.com', port=50001, compress=True, chunk_size=1350))

# Memcache
mc = memcache.Client(['127.0.0.1:11211'], debug=0)
terminal_status_cache = {}

# Statement List
statement_list = []

def getlatestfilefromS3(s3bucket, element_type, datepath):
	output = runS3Query('s3cmd ls '+s3bucket+element_type+datepath)
	fmt_output = str(output).split()
	print fmt_output
	file_list = []
	latest_file_in_s3 = fmt_output[-1]
	latest_ts_in_s3 = fmt_output[-3]

	logging.info('Latest file in s3: {} @ {}'.format(latest_file_in_s3, latest_ts_in_s3))

	# Get last file uplaoded to the bucket
	getfileresult = runS3Query('s3cmd get '+ latest_file_in_s3 +' /root/hts-stats/')
	if '100%' in getfileresult:
		logging.info('s3cmd get: Success!')
	else:
		logging.warning('s3cmd get: Failure!')

	file_list.append(latest_file_in_s3.split('/')[-1].replace('.gz',''))

	# If there are more than one file uplaoded at the same time.
	if fmt_output.count(latest_ts_in_s3) > 1:
		logging.info('More then one file with the same timestamp!')
		logging.info('Second latest file in s3: {} @ {}'.format(fmt_output[-5], fmt_output[-7]))
		getfileresult = runS3Query('s3cmd get '+ fmt_output[-5] + ' /root/hts-stats/')
		if '100%' in getfileresult:
			logging.info('s3cmd get: Success!')
		else:
			logging.warning('s3cmd get: Failure!')

		file_list.append(fmt_output[-5].split('/')[-1].replace('.gz',''))

	os.system('gzip -d /root/hts-stats/*.gz')
	return file_list

def parse_beam_file(latestfile):
	statement_list = []

	with open(latestfile, 'r') as csvfile:
		for line in csvfile:

			line_list = line.replace('"','').strip('\n\r').split(',')

			beam = line_list[0].replace(' ','')
			measurement_name = line_list[1]
			measurement_value = line_list[2]
			ts =  line_list[3]

			add_statement('{},beam={} value={} {}\n'.format(measurement_name,beam,measurement_value,ts))

def parse_gsp_file(latestfile):
	statement_list = []

	# Parse file it will be in the same directory as the source code
	with open(latestfile, 'r') as csvfile:
		for line in csvfile:
			line_list = line.replace('"','').strip('\n\r').split(',')

			gsp = line_list[0]
			measurement_name = line_list[1]
			measurement_value = line_list[2]
			ts =  line_list[3]

			add_statement('{},gsp={} value={} {}\n'.format(measurement_name,gsp,measurement_value,ts))

def parse_inet_file(latestfile):
	statement_list = []

	# Parse file it will be in the same directory as the source code
	with open(latestfile, 'r') as csvfile:
		for line in csvfile:
			line_list = line.replace('"','').strip('\n\r').split(',')

			inet = line_list[0].replace(" ","")
			measurement_name = line_list[1]
			measurement_value = line_list[2]
			ts =  line_list[3]

			# Meta tags
			sat = inet.replace('-','.').split('.')[2]

			add_statement('{},sat={},inet={} value={} {}\n'.format(measurement_name,sat,inet,measurement_value,ts))


def parse_sspc_file(latestfile):
	statement_list = []

	# Parse file it will be in the same directory as the source code
	with open(latestfile, 'r') as csvfile:
		for line in csvfile:
			try:
				line_list = line.replace('"','').replace(' ','').strip('\n\r').split(',')

				terminal_id = line_list[0].split(':')[0].split('-')[-1]
				sspc_name = line_list[0].split(':')[1]
				measurement_name = line_list[1]
				measurement_value = line_list[2]

				ts =  line_list[3]
				if len(str(terminal_id)) == 8:
					if 'SSPP1-KVH_Mgmt_Netsspc_gsp' in terminal_status_cache[terminal_id]:
						gsp = terminal_status_cache[terminal_id]['SSPP1-KVH_Mgmt_Netsspc_gsp'][0]
					else:
						gsp = 'N/A'
						logging.debug('parse_sspc_file(): No cached mgmt sspc for terminal_id {}'.format(terminal_id))

					if 'term_satellite_id' in terminal_status_cache[terminal_id]:
						sat = terminal_status_cache[terminal_id]['term_satellite_id'][0]
					else:
						sat = 'N/A'
						logging.debug('parse_sspc_file(): No cached sat for terminal_id {}'.format(terminal_id))

					if 'term_beam_id' in terminal_status_cache[terminal_id]:
						beam = terminal_status_cache[terminal_id]['term_beam_id'][0]
					else:
						beam= 'N/A'
						logging.debug('parse_sspc_file(): No cached beam for terminal_id {}'.format(terminal_id))

					add_statement('{},terminal_id={},sspc={},gsp={},sat={},beam={} value={} {}\n'.format(measurement_name,terminal_id,sspc_name,gsp,sat,beam,measurement_value,ts))
				else:
					logging.critical('Malformed terminal_id found: {}'.format(terminal_id))
			except:
				continue
def parse_terminal_file(latestfile):
	statement_list = []

	# Parse file it will be in the same directory as the source code
	with open(latestfile, 'r') as csvfile:
		for line in csvfile:
			try:
				entered = 0
				line_list = line.replace('"','').strip('\n\r').split(',')

				terminal_id = line_list[0]
				measurement_name = line_list[1]
				measurement_value = line_list[2]
				ts =  line_list[3]

				if len(str(terminal_id)) == 8:
					if 'SSPP1-KVH_Mgmt_Netsspc_gsp' in terminal_status_cache[terminal_id]:
						gsp = terminal_status_cache[terminal_id]['SSPP1-KVH_Mgmt_Netsspc_gsp'][0]
					else:
						gsp = 'N/A'
						logging.debug('parse_terminal_file(): No cached mgmt sspc for terminal_id {}'.format(terminal_id))

					if 'term_satellite_id' in terminal_status_cache[terminal_id]:
						sat = terminal_status_cache[terminal_id]['term_satellite_id'][0]
					else:
						sat = 'N/A'
						logging.debug('parse_terminal_file(): No cached sat for terminal_id {}'.format(terminal_id))

					if 'term_beam_id' in terminal_status_cache[terminal_id]:
						beam = terminal_status_cache[terminal_id]['term_beam_id'][0]
					else:
						beam= 'N/A'
						logging.debug('parse_terminal_file(): No cached beam for terminal_id {}'.format(terminal_id))

					if 'modcod' in measurement_name:
						if 'us' in measurement_name:
							mc_output = int_to_modcod(int(measurement_value),1)
						else:
							mc_output = int_to_modcod(int(measurement_value),0)
						measurement_value='"'+mc_output+'"'
					add_statement('{},terminal_id={},gsp={},sat={},beam={} value={} {}\n'.format(measurement_name,terminal_id,gsp,sat,beam,measurement_value,ts))
				else:
					logging.critical('Malformed terminal_id found: {}'.format(terminal_id))
			except:
				continue

def int_to_modcod(modcod_as_int,is_up):
	if is_up:
		mc_lookup = us_modcod
	else:
		mc_lookup = ds_modcod
	mc_output =[]
	index_output=[]
	def bits(n):
		while n:
			b = n & (~n+1)
			yield b.bit_length()-1
			n ^= b
	for index in bits(modcod_as_int):
		mc_output.append(mc_lookup[index])

	return ",".join(mc_output)

def add_statement(statement):
	statement_list.append(statement)

def load_terminal_status_cache():
	try:
		term_status_cache = pickle.loads(mc.get('TerminalCache'))
	except:
		logging.warning('terminal_status_cache not found')
		term_status_cache = {}
	return term_status_cache

def send_data(Data):
	influxpost = requests.post("http://influx.ops.kvh.com:8086/write?db=HTS_DEV&precision=s", data=Data)
	if influxpost.status_code != 204:
		logging.warning('Influx Status Code: {}'.format(influxpost.status_code))
		logging.warning('Influx Post Text: {}'.format(influxpost.text))
	else:
		logging.info('Influx Status Code: {}'.format(influxpost.status_code))

def runS3Query(cmd):
	return subprocess.check_output(cmd, shell=True)

if __name__ == "__main__":
	try:
		os.system('rm /root/hts-stats/*.csv')

		datepath = datetime.datetime.now().strftime('/%Y/%m/%d/')

		# Load memcache
		terminal_status_cache = load_terminal_status_cache()
		#pprint(terminal_status_cache['10402947'])
		file_list = []

		for element in element_list:
			file_list += getlatestfilefromS3(s3bucket, element, datepath)

		# Log all files about to be processed
		logging.debug('Files to be processed: {}'.format(file_list))

		for file in file_list:
			logging.debug('File being processed: {}'.format(file))
			if 'beam' in file:
				parse_beam_file('/root/hts-stats/'+file)
			elif 'gsp' in file:
				parse_gsp_file('/root/hts-stats/'+file)
			elif 'inet' in file:
				parse_inet_file('/root/hts-stats/'+file)
			elif 'sspc' in file:
				parse_sspc_file('/root/hts-stats/'+file)
			elif 'terminal' in file:
				parse_terminal_file('/root/hts-stats/'+file)
			else:
				logging.warning('Unknown file type... Not processed')

		# Convert statement_list into influx payload
		payload = "".join(statement_list)

		print payload

		send_data(payload)
		send_hb()
	except Exception as e:
		logging.warning('hts-stats encountered: {}'.format(e))
		print traceback.format_exc()
		os.system('rm /root/hts-stats/*.csv')
