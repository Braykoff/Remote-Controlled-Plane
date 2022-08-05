'''
Gets Playstation 4 remove input from user through local webserver
Also streams cameras (see: CameraServer.py)
'''

## Imports
from subsystems.ControllerServer import ControllerServer

## Declaration
class DualShock4Server:
	## Fix Y Axes Inversion
	def fixAxisInversion(self, index, value):
		if "Y" in self.__axesList[int(index)]:
			return -value
		return value

	## Button and Axis Listener
	def __initialPacket(self, content):
		for index, val in enumerate(content["buttons"]):
			self.buttons[self.__buttonList[index]] = val

		for index, val in enumerate(content["axes"]):
			self.axes[self.__axesList[index]] = self.fixAxisInversion(index, val)

		self.hasController = True

	def __packet(self, content):
		for k, v in content["buttons"].items():
			self.buttons[self.__buttonList[int(k)]] = v

			for l in self.__buttonListeners[self.__buttonList[int(k)]]:
				self.__runListener(l, v, k)

		for k, v in content["axes"].items():
			v = self.fixAxisInversion(k, v)
			self.axes[self.__axesList[int(k)]] = v

			for l in self.__axesListeners[self.__axesList[int(k)]]:
				self.__runListener(l, v, k)


	## Attach/Run Listeners
	def __runListener(self, listener, value, key):
		try:
			listener(value)
		except Exception as e:
			self.logger.addWarning(f"Could not run listener (listener: {key} {listener}, value: {value}): {e}")

	def addButtonListener(self, button, listener):
		if not button in self.__buttonList:
			self.logger.addError(f"Attemtped to add listener {key} {listener} to unknown button '{button}'")
			return False

		self.__buttonListeners[button].append(listener)
		self.__runListener(listener, self.buttons[button], button)
		return True

	def addAxesListener(self, axis, listener):
		if not axis in self.__axesList:
			self.logger.addError(f"Attemtped to add listener {listener} to unknown axes '{axis}'")
			return False

		self.__axesListeners[axis].append(listener)
		self.__runListener(listener, self.axes[axis], axis)
		return True

	## Init
	def __init__(self, host, port, logger):
		self.logger = logger

		## Create Buttons and Axes
		self.__buttonList = ["x", "circle", "square", "triangle", "l1", "r1", "l2", "r2", "share", "options", "lJoystick", "rJoystick", "up", "down", "left", "right", "psButton", "touchpad"]
		self.__axesList = ["leftX", "leftY", "rightX", "rightY", "r2"]

		self.__buttonListeners = {}
		self.__axesListeners = {}

		self.buttons = {}
		self.axes = {}

		for x in range(0, len(self.__buttonList)):
			self.buttons[self.__buttonList[x]] = False
			self.__buttonListeners[self.__buttonList[x]] = []

		for x in range(0, len(self.__axesList)):
			self.axes[self.__axesList[x]] = 0.0
			self.__axesListeners[self.__axesList[x]] = []

		## Create (Flask) App
		self.app = ControllerServer("DualShock4Server", host, port, "gamepad.html", logger)
		self.app.addDefaultPaths()
		self.app.addPacketHandler(self.__initialPacket, self.__packet)
		self.hasController = False


	## Add Camera Server
	def addCameraServer(self, server):
		self.app.addCameraServer(server)

	## Execute Server
	def run(self, restart=False):
		if self.app.running:
			self.logger.addWarning(f"Server is already running! (Restart is {restart})")
			if not restart:
				return

		self.app.run()
