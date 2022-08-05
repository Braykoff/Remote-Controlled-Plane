#! /usr/bin/env python3
'''
Main program controlling the RC aircraft
'''

## Imports
from subsystems.PhysicalController import PhysicalController
from subsystems.GamepadServer import DualShock4Server
from subsystems.CameraServer import CameraServer
from subsystems.Logger import Logger

## Declarations
log = Logger()
physical = PhysicalController(log)
controller = DualShock4Server("0.0.0.0", 5000, log)
camera1 = CameraServer(0, log)

## Add Camera(s)
controller.addCameraServer(camera1)

## Y Axis Inversion
yInverted = True

def invertControls(down):
	global yInverted
	if down:
		yInverted = not yInverted
		log.addMessage(f"Controls inverted (inverted: {yInverted})")

controller.addButtonListener("options", invertControls)

## Set Ailerons
def refreshAilerons():
	#log.addMessage("leftY: {}, rightX: {}".format(controller.axes["leftY"], controller.axes["rightX"]))
	if abs(controller.axes["leftY"]) > abs(controller.axes["rightX"]):
		## Go Up/Down
		i = (-1) if yInverted else (1)

		#physical.setLeftAileron((controller.axes["leftY"]*i)*-45)
		#physical.setRightAileron((controller.axes["leftY"]*i)*-45)
		physical.setLeftAileron(0)
		physical.setRightAileron(0)
	elif abs(controller.axes["leftY"]) < abs(controller.axes["rightX"]):
		## Go Right/Left
		physical.setLeftAileron(controller.axes["rightX"]*-45)
		physical.setRightAileron(controller.axes["rightX"]*45)
	elif controller.axes["leftY"] == 0 and controller.axes["rightX"] == 0:
                ## Both Off
                physical.setLeftAileron(0)
                physical.setRightAileron(0)

## Up/Down Control
def yAxis(val):
	val = (-val) if yInverted else (val)

	physical.setHorizontalStabilizer(val*45)
	refreshAilerons()

controller.addAxesListener("leftY", yAxis)

## Left/Right Control (Only Affects Ailerons)
controller.addAxesListener("rightX", lambda _: refreshAilerons())

## Prop Speed
controller.addAxesListener("r2", lambda val: physical.setProp(val))

## Disable
def disable(val):
	if val:
		physical.toggleDisabled()

controller.addButtonListener("touchpad", disable)

## Run
controller.run()
