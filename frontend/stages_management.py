import time
import json
import requests
import subprocess
from datetime import date
from requests.exceptions import Timeout

from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

from utils.user import User
from utils.utils import log, mv_back, mv_next, mv_next_create
import utils.config as conf


if (conf.prod_models):
	from backend.generer_poesie import load_models
	from backend.adapt_with_models import adapt_poem_with_models, load_roberta_models
	from backend.make_it_rhyme import make_it_rhyme
	#needed the first time at least
	import nltk
	nltk.download('punkt')


# loading widget instructions
# (with respect to UTF-8 bug on windows)
# https://github.com/kivy/kivy/issues/4003
with open('frontend/widgets.kv', encoding='utf8') as f:
    Builder.load_string(f.read())
with open('frontend/screens_management.kv', encoding='utf8') as f:
    Builder.load_string(f.read())


#debug tool to navigate forward and backward in between screens
class NavigationBar(BoxLayout):
	pass


#Entry point (basic welcome screen) of the application
class EntryScreen(Screen):
	def __init__(self, **kwargs):
		super(EntryScreen, self).__init__(**kwargs)
		log("START: the application")
		Clock.schedule_once(self.start_and_switch, 2)
		#1 second elapse time, allowing the UI to finish rendering BEFORE loading models

	def start_and_switch(self, dt):
		self.btn_start()

	def btn_start(self):
		_name = "WelcomeScreen"
		if (conf.prod_models):
			log ("START: LOAD the models")
			_main_model = load_models(conf.MAIN_MODEL, path=conf.MODELS_GENERAL_PATH)
			_thematic_models = load_roberta_models(conf.THEMATIC_ROBERTA_MODELS)
			_emotion_models = load_roberta_models(conf.EMOTION_ROBERTA_MODELS)
			log ("START: models LOADED")
		else:
			log ("START: without models loaded")
			_main_model = ""
			_thematic_models = ""
			_emotion_models = ""
		mv_next_create(self.manager, _name, WelcomeScreen(name=_name,
			main_model=_main_model,
			thematic_models=_thematic_models,
			emotion_models=_emotion_models))


#Login screen
class WelcomeScreen(Screen):
	def __init__(self, main_model, thematic_models, emotion_models, **kwargs):
		super(WelcomeScreen, self).__init__(**kwargs)
		log ("WELCOME: new user")
		#auto login - prepares a valid connected user
		self.user = User()
		self.main_model = main_model
		self.thematic_models = thematic_models
		self.emotion_models = emotion_models
		user_id = self.user.login_auto(conf.prod_database)
		log ("WELCOME: new user gets ID " + user_id)
		if not conf.prod_graphics:
			#self.feedback.text = "Identifiant : " + user_id
			pass

	def start_auto(self, btn):
		from frontend.stage_1_generation import StageGenerationScreen

		#acknowledge a real start of a real human using the app
		#it creates the real local log file with the timestamp at this very moment (initially it logged it in DB)
		self.user.start_auto()

		_name = "StageGenerationScreen"
		mv_next_create(self.manager, _name, StageGenerationScreen(name=_name,
			user=self.user,
			main_model=self.main_model,
			thematic_models=self.thematic_models,
			emotion_models=self.emotion_models,
			state={}))


#Final stage: last view and print
class StageFinalScreen(Screen):
	restarted = False
	#poem contains: raw text, poem_format: renderable with font, font: relative path to exact font
	def __init__(self, user, main_model, thematic_models, emotion_models, state, **kwargs):
		super(StageFinalScreen, self).__init__(**kwargs)
		log ("FINAL: user finished with ID: " + user.getID())

		self.user = user
		self.main_model = main_model
		self.thematic_models = thematic_models
		self.emotion_models = emotion_models
		self.poem = state.get("poem", "")
		self._txt_poem.text = state.get("poem_format", "")
		self.graisse = state.get("graisse", 10)
		self.contraste = state.get("contraste", 50)
		self.rigidite = state.get("rigidite", 0)
		self.font = state.get("font", "")

		#self._user_id.text = "Identifiant utilisateur: " + user.getID()
		self._user_id.text = ""

		#no cancelation possible yet
		Clock.schedule_once(self.publish, 1)
		Clock.schedule_once(self.restart, 120) # 2 minutes

	def publish(self, dt):
		log ("FINAL: print & web will be sent, if activated")
		if (conf.prod_showroom_print):
			self.showroom_printer()
		if (conf.prod_print):
			self.printout()
		if (conf.prod_web):
			self.websent()
			
	def showroom_printer(self):
		# WARNING: First you'll need to install the printer "FOLLOWME_PS" on this machine (for IICT Showroom)
		print_cmd = subprocess.getoutput(f'echo "{self.poem}" | iconv -c -f utf-8 -t ISO-8859-1 | enscript -B -f ZapfChancery-MediumItalic22 -X 88591 --baselineskip=3 --margins=80:10:200:10 --word-wrap -d FOLLOWME_PS')
		log(f"showroom print: {print_cmd}")

	def printout(self):
        # print to a large printer designed for the 2020 exhibition
		code = self.user.getID()
		app_data = {
			"poem": self.poem,
			"graisse": self.graisse,
			"contraste": self.contraste,
			"rigidite": self.rigidite
		}
		app_headers = { "Content-Type": "application/json" }
		try:
			r = requests.post(conf.ENDPOINT_MAC_MINI,
					data=json.dumps(app_data),
					headers=app_headers,
					timeout=conf.TIMEOUT_LOCAL
				)
			log ("printout: sucess with code: " + str(code))
			log (r)
		except Timeout:
			log ("printout: FAILED TIMEOUT with code: " + str(code))
			pass
		except requests.exceptions.RequestException as e:
			print(e)
			pass

	def websent(self):
        # post to a website which was designed to store all create poems (for 2020 exhibition)
		code = self.user.getID()
		app_data = {
			"code": code,
			"text": self.format_poem_as_html(code, self.poem)
		}
		app_headers = { "Content-Type": "application/json" }
		try:
			r = requests.post(conf.ENDPOINT_DL2020_BACKEND,
					data=json.dumps(app_data),
					headers=app_headers,
					timeout=conf.TIMEOUT_EXTERNAL
				)
			log ("Websent: sucess with code: " + str(code))
			log (r)
		except Timeout:
			log ("Websent: FAILED TIMEOUT with code: " + str(code))
			pass
		except requests.exceptions.RequestException as e:
			print(e)
			pass

	def format_poem_as_html(self, code, poem):
		today = date.today()
		month_names = ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',\
						'août', 'septembre', 'octobre', 'novembre', 'décembre']
		formatted_poem = '<!DOCTYPE html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<title>Poème '\
							+ str(code)\
							+ '</title>\n</head>\n'\
							+ '<body style="background-color:black; color:lightgray; letter-spacing:1.5px; font-family:serif;">\n'\
							+ '<p>&nbsp;</p><h2 style="text-align: center;">Poème créé par ' + str(code) + '<br/>le ' + str(today.day)\
							+ ' ' + month_names[today.month] + ' ' + str(today.year)\
							+ '</h2>\n<table align="center" cellpadding="15pt"><tr><td>\n'
		formatted_poem += ('<pre><span style="font-family:serif">'\
							+ poem.replace('[','<').replace(']','>')\
							+ '</span></pre>\n<br/><hr/>\n')
		formatted_poem += '</td></tr></table>\n</body>\n</html>'
		return formatted_poem

	def restart(self, btn):
		if not self.restarted:
			log ("FINAL: user logs out and restart")
			self.restarted = True
			_name = "WelcomeScreen"
			mv_next_create(self.manager,
				_name,
				WelcomeScreen(name=_name,
				main_model=self.main_model,
				thematic_models=self.thematic_models,
				emotion_models=self.emotion_models))
