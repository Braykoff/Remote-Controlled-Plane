'''
Used to log info, messages, and errors to the webserver.
'''
## Imports
from datetime import datetime
import json

## Declaration
class Logger:
	## Constructor
	def __init__(self):
		self.messages = []

	## Get Version
	def version(self):
		return len(self.messages)

	## Add Value (Private Method)
	def __add(self, msg, level):
		self.messages.append({
			"time": datetime.now().strftime("%H:%M:%S"),
			"level": str(level),
			"message": str(msg),
		})

	## Add Message
	def addMessage(self, msg):
		self.__add(msg, "message")

	## Add Warning
	def addWarning(self, msg):
		self.__add(msg, "warning")

	## Add Error
	def addError(self, msg):
		self.__add(msg, "error")

	## Get JSON
	def getJSON(self):
		return json.dumps(self.messages)
