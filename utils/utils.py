import time
from kivy.logger import Logger

import utils.config as conf

def log(s):
	if (conf.prod_log_terminal):
		Logger.info (time.strftime("%H.%M.%S ", time.localtime()) + s)

# move to back screen (no deletion of current screen)
def mv_back(mgr):
	c = mgr.current
	if (__entry == c):
		log("BACK: not moved from " + c)
		pass
	else:
		log("BACK: switched back from " + c)
		mgr.transition.direction = 'right'
		mgr.current = mgr.previous()
		log("to: " + mgr.current)

#move to next screen (no creation of next screen)
def mv_next(mgr):
	n = mgr.next()
	c = mgr.current
	if (__entry == n):
		log("NEXT: not moved from " + c)
		pass
	else:
		log("NEXT: switched forward from " + c)
		mgr.transition.direction = 'left'
		mgr.current = mgr.next()
		log("to: " + mgr.current)

#creates a new screen (if not exists) and moves to next
# WARNING: only moves to the newly created if current position already at end of list - only suitable for forward-backward list
def mv_next_create (mgr, next_screen, widget):
	debug_transition = False
	if debug_transition:
		if (mgr.has_screen(next_screen)): #already exists (check if really reusable?)
			pass
		else: #create new widget
			mgr.add_widget(widget)
		mv_next(mgr)
	else:
		log("SCREEN: moving FROM " + mgr.current)
		mgr.switch_to(widget)
		log("SCREEN: moving TO " + mgr.current)
