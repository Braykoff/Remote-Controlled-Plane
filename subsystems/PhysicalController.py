'''
Control all the physical components on the plane.
Servos, Motors
'''

from easygopigo3 import EasyGoPiGo3
from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory
from threading import Thread
import pigpio
import time

class PhysicalController:
	## Arm Prop
	def __armProp(self):
		self.log.addMessage("Arming propeller...")
		self.pi.set_servo_pulsewidth(self.propPin, 0)
		time.sleep(1)
		self.pi.set_servo_pulsewidth(self.propPin, 700)
		time.sleep(1)
		self.propReady = True
		self.log.addMessage("Armed propeller")

	## Init
	def __init__(self, log):
		self.log = log
		self.disabled = False

		## Ailerons
		self.gpg = EasyGoPiGo3()

		self.ailerons = [self.gpg.init_servo("SERVO1"), self.gpg.init_servo("SERVO2")]

		## Horizontal Stabilizer
		self.gpioFactory = PiGPIOFactory()
		self.horizontalStabilizer = AngularServo(17, pin_factory=self.gpioFactory, min_pulse_width=0.0006, max_pulse_width=0.0023)

		## Set Prop
		self.propReady = False
		self.pi = pigpio.pi()
		self.propPin = 27

		self.armThread = Thread(target = self.__armProp)
		self.armThread.start()

	## Clamp Inputs
	def __clamp(self, value, kMIN, kMAX):
		if value > kMAX or value < kMIN:
					self.log.addWarning(f"Speed ({value}) was not within range ({kMIN} - {kMAX}), so it has been clamped")
		return max(min(value, kMAX), kMIN)

	## Set Ailerons
	def __setAileron(self, aileron, angle):
		if self.disabled:
			self.log.addWarning("Did not set {} aileron because motors are disabled".format("left" if aileron == 0 else "right"))
			return
		self.ailerons[aileron].rotate_servo(self.__clamp(angle, -90, 90)+90)

	def setLeftAileron(self, angle):
		self.__setAileron(0, angle+15)

	def setRightAileron(self, angle):
		self.__setAileron(1, -angle)

	## Set Horizontal Stabilizer
	def setHorizontalStabilizer(self, angle):
		if self.disabled:
			self.log.addWarning("Did not set horizontal stabilizer because motors are disabled")
			return
		self.horizontalStabilizer.angle = self.__clamp(-angle, -90, 90)

	## Set Front Propellor
	def __normalizePropSpeed(self, val): # normalize speed from range of 0 - 1 to 700 - 2000
		return (1300)*(val)+700

	def setProp(self, speed):
		if self.propReady != True:
			self.log.addWarning("Prop is not yet ready...")
			return

		if self.disabled:
			self.log.addWarning(f"Did not set prop speed to {speed} because motors are disabled")
			return

		speed = self.__normalizePropSpeed(self.__clamp(speed, 0, 1))

		if speed == 700:
			self.pi.set_servo_pulsewidth(self.propPin, 0)
		else:
			self.pi.set_servo_pulsewidth(self.propPin, speed)

	## Set Disabled
	def toggleDisabled(self):
		self.disabled = not self.disabled
		if self.disabled and self.propReady:
			self.pi.set_servo_pulsewidth(self.propPin, 0)

		self.log.addMessage(f"Disabled toggled, now is: {self.disabled}")
