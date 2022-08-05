'''
Streams the current energy voltage, as a graph
'''
from threading import Thread
import cv2

class Energy:
	## Init
	def __init__(self, logger):
		self.log = logger
