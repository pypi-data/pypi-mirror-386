#!/usr/bin/python3
#
#--------------------------------------
#
# RaspController notifications
# v.6
#
# Author   : Ettore Gallina
# Date     : 23/10/2025
# Copyright: Egal Net di Ettore Gallina
#
# https://www.egalnetsoftwares.com/
#
#--------------------------------------

"""
This module provides a Python wrapper for the RaspController notification library.

It allows you to send push notifications from your Raspberry Pi 
(or other compatible device) to the RaspController mobile application.
"""


import ctypes
import subprocess
import os



# --- Dynamic Library Loading ---
# This section automatically determines which compiled C library to load.
# It checks if the system is 32-bit or 64-bit and which version of OpenSSL
# is installed, then loads the compatible library file.

_long_bit = subprocess.check_output(["getconf", "LONG_BIT"]).decode("utf-8").strip()
_openssl_version = subprocess.check_output(["openssl", "version"]).decode("utf-8").strip()
if _long_bit == "64":
	if _openssl_version.startswith("OpenSSL 1.1.1"):
		_lib_so = "raspc_notif_lib3_arm64_ssl1.1.1.so"
	elif _openssl_version.startswith("OpenSSL 3."):
		_lib_so = "raspc_notif_lib3_arm64_ssl3.0.11.so"
	else:
		raise Exception("OpenSSL not found or incompatible version")
elif _long_bit == "32":
	if _openssl_version.startswith("OpenSSL 1.1.1"):
		_lib_so = "raspc_notif_lib3_armhf_ssl1.1.1.so"
	elif _openssl_version.startswith("OpenSSL 3."):
		_lib_so = "raspc_notif_lib3_armhf_ssl3.0.11.so"
	else:
		raise Exception("OpenSSL not found or incompatible version")
else:
	raise Exception("LONG_BIT does not have a valid value: {0}".format(long_bit))
_notif_lib = ctypes.cdll.LoadLibrary(os.path.dirname(os.path.abspath(__file__)) + os.path.sep + _lib_so)	

		
     
class _CResult(ctypes.Structure):
	"""
	A Ctypes structure that maps to the result object returned by the C library.
	This is used internally to translate the C data into a Python object.
	"""
	_fields_ = [("status", ctypes.c_int),
                ("message", ctypes.c_char_p)] 
		

class Result:
	"""
	Represents the result of a notification sending operation.
	
	It contains a status code (e.g., SUCCESS, SOCKET_ERROR) and a 
	descriptive message from the library.
	"""
	
	# --- Status Constants ---
	SUCCESS = ctypes.c_int.in_dll(_notif_lib, "SUCCESS").value
	SOCKET_ERROR = ctypes.c_int.in_dll(_notif_lib, "SOCKET_ERROR").value
	TOO_MANY_REQUESTS = ctypes.c_int.in_dll(_notif_lib, "TOO_MANY_REQUESTS").value
	SERVER_ERROR = ctypes.c_int.in_dll(_notif_lib, "SERVER_ERROR").value
	INVALID_APIKEY = ctypes.c_int.in_dll(_notif_lib, "INVALID_APIKEY").value
	INVALID_PARAMETER = ctypes.c_int.in_dll(_notif_lib, "INVALID_PARAMETER").value
	NO_TOKEN_FOUND = ctypes.c_int.in_dll(_notif_lib, "NO_TOKEN_FOUND").value
		
		
	def __init__(self, status, message):
		"""
		Initializes the Result object.
		
		Args:
			status (int): The status code returned by the library.
			message (str): The descriptive result message.
		"""
		self.status = status
		self.message = message
		
		
		
class Notification:
	"""
	A data class that holds the content for a single notification.
	"""
	
	def __init__(self, title, message, high_priority = False):
		"""
		Initializes the Notification object.
		
		Args:
			title (str): The title of the notification (max 200 chars). 
			             Can be None for no title.
			message (str): The main body of the notification (max 1000 chars).
			               This field is required and cannot be empty.
			high_priority (bool): (only Android) Whether to send as a high-priority notification.
			                      Defaults to False.
		"""
		self.title = title
		self.message = message
		self.high_priority = high_priority
		
	def has_valid_title(self):
		"""Checks if the title is valid (is None or a string)."""
		return self.title == None or isinstance(self.title, str)


	def has_valid_message(self):
		"""Checks if the message is valid (is a non-empty string)."""
		return isinstance(self.message, str) and self.message.strip()
		
		

class Sender:
	"""
	The main class for sending notifications.
	
	It requires an API key to authenticate with the 
	RaspController notification service.
	"""
	
	def __init__(self, apikey):
		"""
		Initializes the Sender.
		
		Args:
			apikey (str): The API key obtained from the RaspController app.
		"""
		self.apikey = apikey


	def send_notification(self, notification):
		"""
		Attempts to send a notification.
		
		It validates the notification object and returns the result.
		
		Args:
			notification (Notification): The Notification object to be sent.
			
		Returns:
			Result: A Result object indicating the status (success or error)
			        of the send operation.
		"""
		if not isinstance(notification, Notification):
			return Result(Result.INVALID_PARAMETER, "Invalid notification")
		
		if not notification.has_valid_title():
			return Result(Result.INVALID_PARAMETER, "Invalid title")

		if not notification.has_valid_message():
			return Result(Result.INVALID_PARAMETER, "Invalid message")
		
		title_to_send = notification.title[0:200].encode()
		message_to_send = notification.message[0:1000].encode()
		cresult = ctypes.POINTER(_CResult)
		_notif_lib.send_notifications.restype = ctypes.POINTER(_CResult)
		cresult = _notif_lib.send_notifications(self.apikey.encode(), title_to_send, message_to_send, notification.high_priority)
		result = Result(cresult.contents.status, cresult.contents.message.decode("utf-8"))
		_notif_lib.free_result(cresult)
		return result


	

		
		
		

  
