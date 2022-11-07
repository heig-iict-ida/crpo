from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.clock import Clock

from utils.utils import log, mv_back, mv_next, mv_next_create
from frontend.stages_management import StageFinalScreen
from frontend.stage_manual_edition import StageManualEditionScreen

import utils.config as conf
if (conf.prod_models):
	from backend.make_it_rhyme import make_it_rhyme

with open('frontend/widgets.kv', encoding='utf8') as f:
	Builder.load_string(f.read())
with open('frontend/screen_4_rhyme.kv', encoding='utf8') as f:
	Builder.load_string(f.read())

stage_name = "4.0-FOUR-RHYME"
#STAGE FOUR (4.0)
#Rhymes
class StageRhymeScreen(Screen):
	_scheme = ""
	first_scheme = ""
	second_scheme = ""
	third_scheme = ""
	params = ""
	txt_intro = "Choose the rhyming scheme that I shall\napply to the poem."
	txt_wait = "Generating rhymes: please wait.\nI am busy with complex calculations."
	txt_wait_poem = "Creation in progress..."
	txt_result = "Here is my proposal: it may not be perfect,\nso feel free to edit it one last time."


	def __init__(self, user, main_model, thematic_models, emotion_models, state, **kwargs):
		super(StageRhymeScreen, self).__init__(**kwargs)
		self.user = user
		self.main_model = main_model
		self.thematic_models = thematic_models
		self.emotion_models = emotion_models
		self._main_txt.text = self.txt_intro
		self._base_poem = state.get("poem", "")
		self._adapted_poem = state.get("adapted_poem", state.get("poem", ""))
		self._txt_poem.text = state.get("displayed_adapted_poem", state.get("poem", ""))
		self._btn_edit.disabled = state.get("buttons_disabled", False)
		self._btn_next.disabled = state.get("buttons_disabled", False)
		self.setSchemeFromPoemStructure(self._base_poem)
		self.old_state = state # Used to remember previous slider values for typhography screen

		self.user.write_file_stage_start(stage_name, self._adapted_poem)

	def setSchemeFromPoemStructure(self, poem):
		strophes = poem.split("\n\n")
		current_char = "A"
		current_scheme = ""

		for i, strophe in enumerate(strophes):
			lines = strophe.split("\n")
			length = len(lines)

			if length == 1:
				self.first_scheme += current_char			# A
				self.second_scheme += current_char			# A
				self.third_scheme += current_char			# A

				if current_char != "Z":
					current_char = chr(ord(current_char) + 1)

			elif length == 2:
				self.first_scheme += current_char + \
					current_char							# AA
				self.second_scheme += current_char + \
					current_char							# AA
				self.third_scheme += current_char + \
					current_char							# AA

				if current_char != "Z":
					current_char = chr(ord(current_char) + 1)

			elif length == 3:
				# Haiku hack
				if self.second_scheme == "ABA ":
					self.first_scheme += "CDC"
					self.second_scheme += "BCB"
					self.third_scheme += "BAB"
					current_char = "E"
				else:
					first_char = current_char
					if current_char != "Z":
						second_char  = chr(ord(first_char) + 1)
					else:
						second_char = "Z"

					self.first_scheme += first_char + \
						second_char + \
						first_char								# ABA
					self.second_scheme += first_char + \
						second_char + \
						first_char								# ABA
					self.third_scheme += first_char + \
						second_char + \
						first_char								# ABA

					if first_char != "Z" and second_char != "Z":
						current_char = chr(ord(current_char) + 2)

			elif length >= 4:
				first_char = current_char
				if current_char != "Z":
					second_char  = chr(ord(first_char) + 1)
				else:
					second_char = "Z"

				self.first_scheme += first_char + \
					second_char + \
					first_char + \
					second_char								# ABAB
				self.second_scheme += first_char + \
					second_char + \
					second_char + \
					first_char								# ABBA
				self.third_scheme += first_char + \
					first_char + \
					second_char + \
					second_char								# AABB

				if first_char != "Z" and second_char != "Z":
					current_char = chr(ord(current_char) + 2)

				length -= 4
				while (length > 0):
					if (length % 2 == 0):
						self.first_scheme += current_char + \
							current_char					# ...CC
						self.second_scheme += current_char + \
							current_char					# ...CC
						self.third_scheme += current_char + \
							current_char					# ...CC
						length -= 2
					else:
						self.first_scheme += current_char	# ...C
						self.second_scheme += current_char	# ...C
						self.third_scheme += current_char	# ...C
						length -= 1

					if current_char != "Z":
						current_char = chr(ord(current_char) + 1)

			self.first_scheme += " "
			self.second_scheme += " "
			self.third_scheme += " "

		self._first_scheme_button.text = self.first_scheme.strip()
		self._second_scheme_button.text = self.second_scheme.strip()
		self._third_scheme_button.text = self.third_scheme.strip()

		self._scheme = self._first_scheme_button.text

		if (self.third_scheme == self.second_scheme):
			self._third_scheme_button.text = ""
			self._third_scheme_button.disabled = True
		if (self.second_scheme == self.first_scheme):
			self._second_scheme_button.text = ""
			self._second_scheme_button.disabled = True

	# DEPRECATED
	def _notify_change_settings(self):
		if (self._scheme != ""): #enable send only if a format has been choosen
			self._btn_gen.disabled = False

	def btn_format(self, btn, txt):
		self._scheme = txt
		self._notify_change_settings()

		#disallow unselection of just selected radio button
		for i in self.togglegroup.children:
			if i.text != "":
				i.disabled = False
		btn.disabled = True

	def btn_rhyme_press(self, btn):
		btn.disabled = True
		self._btn_edit.disabled = True
		self._btn_next.disabled = True
		self.ui_able()

		self._main_txt.text = self.txt_wait
		self._txt_poem.text = self.txt_wait_poem

	def btn_rhyme_release(self, btn):
		Clock.schedule_once(self.rhyme, 0.1)

	def ui_able(self, disabled = True):
		for i in self.togglegroup.children:
			i.disabled = disabled
			#disable the currently selected toggle button to mimic real radio button (no-selection is impossible)
			if (i.state == 'down' and disabled == False):
				i.disabled = True

	def rhyme(self, dt):
		text = ""
		scheme = str(self._scheme).upper()
		self.params = '['+ scheme + ']'
		if (conf.prod_models):
			#actual interaction (with actual values for format and mixing numbers)
			result = make_it_rhyme(poem=self._base_poem,
				models=self.main_model,
				rhyming_scheme=scheme,
				n_candidates=30, # or 100 ?
				rime_syllables=2) # or 1
		else:
			text = self._base_poem \
			+ "\nStage FOUR 4.0 : Rhymes"  \
			+ "\n Rhyming scheme:" + scheme
			result = (text, text)

		self._btn_gen.disabled = False
		self._btn_edit.disabled = False
		self._btn_next.disabled = False
		self.ui_able(disabled = False)

		self._txt_poem.text = result[0]
		self._adapted_poem = result[1]
		self._main_txt.text = self.txt_result
		self._btn_gen.text = "Regenerate the rhymes"

		# write the intermediate result from back-end
		self.user.write_file_stage_interm(stage_name, self._adapted_poem, v_param = self.params)


	def btn_edit(self, btn):
		btn.disabled = True

		#No write needed here - see stage_1 for full comment.

		#move forward to next stage
		_name = "StageManualEditionScreen"
		current_state = {
			"poem": self._adapted_poem,
			"base_poem": self._base_poem,
			"adapted_poem": self._adapted_poem,
			"displayed_adapted_poem": self._txt_poem.text,
			"origin": 4
		}
		mv_next_create(self.manager,
			_name,
			StageManualEditionScreen(name=_name,
				user=self.user,
				main_model=self.main_model,
				thematic_models=self.thematic_models,
				emotion_models=self.emotion_models,
				state=current_state))


	
	def btn_next(self, btn):
		btn.disabled = True

		self._txt_poem.text = self._txt_poem.text.replace("[u]", "")
		self._txt_poem.text = self._txt_poem.text.replace("[/u]", "")
		
		#Write the current version as definitive.
		#TWO writes are needed for the exact same reason as in the start (see above)
		#Keep in mind that the params stored here may, or may not, be the one suggested by the system at first, 
        # or some results of a "reset" (new suggestion button hit), or used-customized.
		self.user.write(self._adapted_poem, v_param = self.params, forward = True)
		#This triggers finalisation of the log.
		self.user.write_file_stage_end(stage_name, self._txt_poem.text, "FINAL")
        
		#move forward to next stage
		_name = "StageFinalScreen"
		current_state = {
			"poem": self._adapted_poem,
			"poem_format": self._txt_poem.text,
			"graisse": 10,
			"contraste": 50,
			"rigidite": 0,
			"font": "utils/fonts/static/dlgx-010-050-000.ttf"
		}
		mv_next_create(self.manager,
			_name,
			StageFinalScreen(name=_name,
				user=self.user,
				main_model=self.main_model,
				thematic_models=self.thematic_models,
				emotion_models=self.emotion_models,
				state=current_state))