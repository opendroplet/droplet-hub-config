#!/usr/bin/python

"""

  All Emoncms code is released under the GNU Affero General Public License.
  See COPYRIGHT.txt and LICENSE.txt.

  ---------------------------------------------------------------------
  Emoncms - open source energy visualisation
  Part of the OpenEnergyMonitor project:
  http://openenergymonitor.org

"""

'''
Modifications by Fake-Name/Connor Wolf
'''

import urllib2, httplib
import logging, logging.handlers
import time
import math

import logging
import sys

import subprocess
import re
import datetime
import os
import signal


"""class ServerDataBuffer

Stores server parameters and buffers the data between two HTTP requests

"""
class ServerDataBuffer():

	def __init__(self, protocol, domain, path, apikey, period, logger=None):
		"""Create a server data buffer initialized with server settings.
		
		protocol (string):  "https://" or "http://"
		domain   (string):  domain name (eg: 'domain.tld')
		path     (string):  emoncms path with leading slash (eg: '/emoncms')
		apikey   (string):  API key with write access
		period   (int):     sending interval in seconds
		logger   (string):  the logger's name (default None)
		
		"""
		self._protocol = protocol
		self._domain = domain
		self._path = path
		self._apikey = apikey
		self._period = period
		self._data_buffer = []
		self._last_send = time.time()
		self._logger = logging.getLogger(logger+".EMon")
		self._logger.debug("Initing EMonCMS interface")


	def add_data(self, data):
		# Append timestamped dataset to buffer.
		# data (list): node and values (eg: '[node,val1,val2,...]')
		
		self._logger.debug("Server " + self._domain + self._path + " -> add data: " + str(data))
		
		self._data_buffer.append(data)

	def send_data(self):
		"""Send data to server."""
		
		# Prepare data string with the values in data buffer
		data_string = ''
		for data in self._data_buffer:
			for sample in data:
				data_string += str(sample)
				data_string += ','
		data_string = data_string[0:-1] # Remove trailing comma and close bracket 
		self._data_buffer = []
		self._logger.debug("Data string: " + data_string)
		
		# Prepare URL string of the form
		# http://localhost:8088/input/post.json?node=1&csv=100,200,300
		# NOT 'http://domain.tld/emoncms/input/bulk.json?apikey=12345&data=[[-10,10,1806],[-5,10,1806],[0,10,1806]]'
		url_string = self._protocol+self._domain+self._path+"/input/post.json?apikey="+self._apikey+"&node=2&csv="+data_string
		self._logger.debug("URL string: " + url_string)

		# Send data to server
		self._logger.info("Sending to " + self._domain + self._path)
		try:
			result = urllib2.urlopen(url_string)
		except urllib2.HTTPError as e:
			self._logger.warning("Couldn't send to server, HTTPError: " + str(e.code))
		except urllib2.URLError as e:
			self._logger.warning("Couldn't send to server, URLError: " + str(e.reason))
		except httplib.HTTPException:
			self._logger.warning("Couldn't send to server, HTTPException")
		except Exception:
			import traceback
			self._logger.warning("Couldn't send to server, Exception: " + traceback.format_exc())
		else:
			if (result.readline() == 'ok'):
				self._logger.info("Send ok")
			else:
				self._logger.warning("Send failure")
		
		# Update _last_send
		#self._last_send = time.time()

	def check_time(self):
		"""Check if it is time to send data to server.
		
		Return True if sending interval has passed since last time

		"""
		now = time.time()
		delta = now - self._last_send
		if (delta > self._period):
			print "Elapsed delta between updates =", delta, "seconds. overshoot =", delta-self._period, "seconds."
			self._last_send = self._last_send + self._period
			return True
	
	def has_data(self):
		"""Check if buffer has data
		
		Return True if data buffer is not empty.
		
		"""
		return (self._data_buffer != [])
	
def initLogging():
	mainLogger = logging.getLogger("Main")			# Main logger
	mainLogger.setLevel(logging.DEBUG)
	
	ch = logging.StreamHandler(sys.stdout)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	ch.setFormatter(formatter)
	mainLogger.addHandler(ch)

def timeout_command(cmdList, timeout):
	#call shell-command and either return its output or kill it
	#if it doesn't normally exit within timeout seconds and return None
	

	start = datetime.datetime.now()
	process = subprocess.Popen(cmdList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	while process.poll() is None:
		time.sleep(0.1)
		now = datetime.datetime.now()
		if (now - start).seconds > timeout:
			print "subprocess timed out. Force-killing it"
			os.kill(process.pid, signal.SIGKILL)
			os.waitpid(-1, os.WNOHANG)
			return None
	return process.stdout.read()

def getDummyDropletData():

	print "Generate Dummy Droplet data"

	dropletFlow = None
	dropletConfidence = None

	dropletFlow = (math.cos(time.time()/10)+1)/2*100
	dropletConfidence = (math.sin(time.time()/5)+1)/2*100

	print "dropletFlow", dropletFlow, "dropletConfidence", dropletConfidence
	return dropletFlow, dropletConfidence

if __name__ == "__main__":
	print "Starting"

	initLogging()

	monBuf = ServerDataBuffer(protocol = 'http://',
							  domain = 'localhost',
							  path = '',
							  apikey = "8174cefd8589b8fce3f712c82ac4a2c8",
							  period = 5,
							  logger="Main")


	while 1:
		if monBuf.check_time():
			print "Ready to send"
			dropletFlowVal, dropletConfidenceVal = getDummyDropletData()
			if dropletFlowVal != None and dropletConfidenceVal != None:
				print "Sending dummy droplet packet"
				monBuf.add_data([dropletFlowVal, dropletConfidenceVal])

			monBuf.send_data()
		time.sleep(0.05)