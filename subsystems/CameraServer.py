'''
For StreamingCameras to the Web Server
'''
import uuid
import cv2

class CameraServer:
	## Init
	def __init__(self, cameraIndex, logger):
		self.logger = logger
		self.cameraIndex = cameraIndex
		self._id = str(uuid.uuid4())
		self.success = True

		self.camera = cv2.VideoCapture(cameraIndex)

		if self.camera is None or not self.camera.isOpened():
			self.logger.addWarning(f"Could not open camera on index {cameraIndex}")
			self.success = False

	## Frame Generator
	def generateFrames(self, webEncoded=False):
		while True:
			s, frame = self.camera.read()

			if not s:
				self.logger.addWarning(f"Camera {self.cameraIndex} could not get next frame (success is {s})")
				self.success = False
				break

			if webEncoded:
				_, buffer = cv2.imencode(".jpg", frame)
				data = buffer.tobytes()
				yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n')
			else:
				yield frame
