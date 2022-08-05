'''
A base class for a Flask server that can receive input from the user
Used By GamepadServer.py to handle network requests
Used so other controller types (keyboard, touchscreen, etc) can be easily created in the future
'''

from flask import Flask, render_template, send_file, request, make_response, Response, Markup, redirect
import threading
import json

class ControllerServer:
	## Init
	def __init__(self, name, host, port, indexPage, logger):
		self.name = name
		self.host = host
		self.port = port
		self.index = indexPage
		self.logger = logger
		self.running = False
		self.thread = None

		self.packetHandler = None
		self.initPacketHandler = None

		self.cameraServers = {}

		self.app = Flask(name, template_folder="static")

	## Raw Text Response
	def txt(self, msg, status=200):
		resp = make_response(str(msg), status)
		resp.mimetype = "text/plain"
		return resp

	## Add Path
	def route(self, path, handler=None, methods=["GET"]):
		if handler == None:
			handler = self.__handleDefaultPath
		self.app.add_url_rule(path, None, handler, methods=methods)

	## Handle Default Path
	def __handleDefaultPath(self, *args, **kwargs):
		path = str(request.path).split("/")
		path.remove("")

		if request.path == "/": # Home
			streams = ""
			keys = sorted(list(self.cameraServers.keys()), key = lambda x: self.cameraServers[x].cameraIndex)
			default = (f"/camera/{keys[0]}") if len(keys) > 0 else ("/resource/noCamera.png")

			for s in keys:
				streams += f"<option value='{s}'>{self.cameraServers[s].cameraIndex} ({s})</option>"

			return render_template(self.index, streams = Markup(streams), defaultStream = default)
		elif len(path) == 2 and path[0] == "resource": # Serve Resource
			try:
				return send_file(f"static/resources/{path[1]}")
			except Exception as e:
				self.logger.addError(f"Could not send resource '{path[1]}': {e}")
				return self.txt(f"Error while sending resource '{path[1]}'", 404)
		elif len(path) == 1 and path[0] == "log": # Send Log (HTML)
			return render_template("log.html")
		elif len(path) == 2 and path[0] == "log" and path[1] == "raw": # Send Log (Raw)
			try:
				version = int(request.args.get("version", -1))
				if version == self.logger.version():
					return self.txt("Up to date", 200)
				elif version > self.logger.version():
					return self.txt(self.logger.version(), 409)
				else:
					return self.txt("{};{}".format(self.logger.version(), self.logger.getJSON()), 206)
			except Exception as e:
				print("Could not send log (version: '{}'): {}".format(request.args.get("version", "Not Specified"), e))
				return self.txt("Could not send log", 500)
		elif len(path) == 1 and path[0] == "camera": # List Cameras
			return self.txt(json.dumps(list(self.cameraServers.keys())))
		elif len(path) == 2 and path[0] == "camera": # Stream Camera
			if not path[1] in self.cameraServers.keys():
				self.logger.addWarning(f"Client requested unknown camera stream '{path[1]}'")
				return self.txt(f"Unknown camera stream: {path[1]}. Check /camera for a full list.")
			try:
				if self.cameraServers[path[1]].success == False:
					return redirect("/resource/noCamera.png")
				return Response(self.cameraServers[path[1]].generateFrames(webEncoded=True), mimetype="multipart/x-mixed-replace; boundary=frame")
			except Exception as e:
				self.logger.addError(f"Could not send camera stream ({path[1]}): {e}")
				return self.txt("Error while streaming camera", 500)

		return self.txt("404: Page Not Found", 404)

	## Add Default Paths
	def __handleError(self, e):
		return self.txt(f"Error: {e}", 500)

	def addDefaultPaths(self):
		self.route("/")
		self.route("/resource/<r>")
		self.route("/log")
		self.route("/camera")

		self.app.register_error_handler(404, self.__handleDefaultPath)
		self.app.register_error_handler(500, self.__handleError)

	## Add Packet Handler
	def __handlePackets(self, initial=False):
		target = (self.initPacketHandler) if (initial) else (self.packetHandler)

		if target == None:
			return self.txt("No handler!", 500)
		else:
			try:
				if initial:
					self.logger.addMessage("A client connected controller '{}'".format(request.headers.get("controllerId", "Unknown")))

				target(json.loads(request.data.decode()))
				return self.txt("Success", 200)
			except Exception as e:
				self.logger.addError(f"Could not receive packet (initial: {initial}): {e}")
				return self.txt("An error occurred. Check the log.", 500)

	def addPacketHandler(self, initialHandler, packetHandler):
		self.initPacketHandler = initialHandler
		self.packetHandler = packetHandler

		self.route("/controller/initialPacket", lambda: self.__handlePackets(True), methods=["POST"])
		self.route("/controller/packet", self.__handlePackets, methods=["POST"])

	## Add CameraServer
	def addCameraServer(self, server):
		if server._id in self.cameraServers.keys():
			self.logger.addWarning(f"Camera Server {server._id} (for camera: '{server.cameraIndex}') added, but already exists!")
			return
		elif server.success == False:
			self.logger.addWarning(f"Did not add Camera Server {server._id} (for camera: '{server.cameraIndex}') because it had an error")
			return

		self.cameraServers[server._id] = server
		self.route("/camera/<c>", self.__handleDefaultPath)

	## Run
	def run(self):
		self.thread = threading.Thread(target = lambda: self.app.run(host=self.host, port=self.port, use_reloader=False, debug=False))
		self.thread.start()
		self.running = True
		self.logger.addMessage(f"'{self.name}' server has started with host '{self.host}' on port {self.port}")
		print(f"'{self.name}' server has started with host '{self.host}' on port {self.port}")
