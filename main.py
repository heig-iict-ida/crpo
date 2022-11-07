#!/usr/bin/python
#coding=utf-8

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager

from utils.utils import log, mv_back, mv_next, mv_next_create
from frontend.stages_management import EntryScreen

__entry = "EntryPoint"


# main application class
class CPAOApp(App):

	def __init__(self, **kwargs):
		super(CPAOApp, self).__init__(**kwargs)
		# initialize new ScreenManager for handling screens
		self.manager = ScreenManager()

	def build(self):
		self.manager.add_widget(EntryScreen(name="EntryPoint"))
		#mv_next(self.manager) #single screen: not useful to move to this screen
		return self.manager

	#forwards commands from app (navigation bar) to global mv code
	def mv_back(self):
		mv_back(self.manager)

	def mv_next(self):
		mv_next(self.manager)


if __name__ == '__main__':
	CPAOApp().run()
