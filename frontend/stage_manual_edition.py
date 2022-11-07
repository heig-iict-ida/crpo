from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.clock import Clock

from utils.utils import log, mv_back, mv_next, mv_next_create

import utils.config as conf

with open('frontend/widgets.kv', encoding='utf8') as f:
	Builder.load_string(f.read())
with open('frontend/screen_manual_edition.kv', encoding='utf8') as f:
	Builder.load_string(f.read())

stage_name = "KEYBOARD MANUAL EDITION"
# INTERMEDIATE STAGE
#Stage - manual edition with keyboard
class StageManualEditionScreen(Screen):
	def __init__(self, user, main_model, thematic_models, emotion_models, state, **kwargs):
		super(StageManualEditionScreen, self).__init__(**kwargs)
		self.user = user
		self.main_model = main_model
		self.thematic_models = thematic_models
		self.emotion_models = emotion_models
		self._txt_poem.text = state.get("poem", "")
		self._txt_orig = state.get("poem", "")
		self.old_state = state
		self.keyboard_open = True
		Clock.schedule_once(self.focus_keyboard, 0.2)

	def focus_keyboard(self, dt):
		self._space.size_hint_y = 5.25 #under the keyboard
		self._space.text = "Touch the poem to bring up the keyboard."
		self._txt_poem.focus = True

	def btn_return(self, btn):
		from screens.stage_1_generation import StageGenerationScreen
		from screens.stage_2_theme import StageThemeScreen
		from screens.stage_3_emotion import StageEmotionScreen
		from screens.stage_4_rhyme import StageRhymeScreen

		btn.disabled = True
		origin = self.old_state.get("origin", -1)
		
		#BY CANCELATION (RETURN), write the current draft version which will be discarded (modified, or not), to get back to the main stage with last original text (which may, or may not, change again)
		self.user.write_file_stage_interm(stage_name, self._txt_poem.text, v_param = "[self-edit-back-cancel]")

		#move to previous screen
		if (origin == 1):
			_name = "StageGenerationScreen"
			current_state = self.old_state
			current_state.update({ "buttons_disabled": False })

			mv_next_create(self.manager,
				_name,
				StageGenerationScreen(name=_name,
					user=self.user,
					main_model=self.main_model,
					thematic_models=self.thematic_models,
					emotion_models=self.emotion_models,
					state=current_state))
		elif (origin == 2):
			_name = "StageThemeScreen"
			current_state = self.old_state
			current_state.update({ "buttons_disabled": False })

			mv_next_create(self.manager,
				_name,
				StageThemeScreen(name=_name,
					user=self.user,
					main_model=self.main_model,
					thematic_models=self.thematic_models,
					emotion_models=self.emotion_models,
					state=current_state))
		elif (origin == 3):
			_name = "StageEmotionScreen"
			current_state = self.old_state
			current_state.update({ "buttons_disabled": False })

			mv_next_create(self.manager,
				_name,
				StageEmotionScreen(name=_name,
					user=self.user,
					main_model=self.main_model,
					thematic_models=self.thematic_models,
					emotion_models=self.emotion_models,
					state=current_state))
		elif (origin == 4):
			_name = "StageRhymeScreen"
			current_state = self.old_state
			current_state.update({ "buttons_disabled": False })

			mv_next_create(self.manager,
				_name,
				StageRhymeScreen(name=_name,
					user=self.user,
					main_model=self.main_model,
					thematic_models=self.thematic_models,
					emotion_models=self.emotion_models,
					state=current_state))
		else:
			log ("MOVEBACK: unsupported origin:" + self.origin)

	def btn_next(self, btn):
		from frontend.stage_2_theme import StageThemeScreen
		from frontend.stage_3_emotion import StageEmotionScreen
		from frontend.stage_4_rhyme import StageRhymeScreen
		from frontend.stages_management import StageFinalScreen

		btn.disabled = True
		origin = self.old_state.get("origin", -1)
		
		##BY CONFIRMATION (NEXT), write the definitive edited text (while UI move to next stage)
		self.user.write_file_stage_end(stage_name, self._txt_poem.text, "NEXT-EDIT")

		#move forward to next stage
		if (origin == 1):
			_name = "StageThemeScreen"
			current_state = {
				"poem": self._txt_poem.text
			}
			mv_next_create(self.manager,
				_name,
				StageThemeScreen(name=_name,
					user=self.user,
					main_model=self.main_model,
					thematic_models=self.thematic_models,
					emotion_models=self.emotion_models,
					state=current_state))
		elif (origin == 2):
			_name = "StageEmotionScreen"
			current_state = {
				"poem": self._txt_poem.text
			}
			mv_next_create(self.manager,
				_name,
				StageEmotionScreen(name=_name,
					user=self.user,
					main_model=self.main_model,
					thematic_models=self.thematic_models,
					emotion_models=self.emotion_models,
					state=current_state))
		elif (origin == 3):
			_name = "StageRhymeScreen"
			current_state = {
				"poem": self._txt_poem.text
			}
			mv_next_create(self.manager,
				_name,
				StageRhymeScreen(name=_name,
					user=self.user,
					main_model=self.main_model,
					thematic_models=self.thematic_models,
					emotion_models=self.emotion_models,
					state=current_state))
			#final: write data to db (and forward)
			self.user.write(self._txt_poem.text, v_param = "self edit", forward = True)

		elif (origin == 4):
			_name = "StageFinalScreen"
			current_state = {
				"poem": self._txt_poem.text,
				"poem_format": self._txt_poem.text,
				"sld1_value": self.old_state.get("sld1_value", 10),
				"sld2_value": self.old_state.get("sld2_value", 50),
				"sld3_value": self.old_state.get("sld3_value", 0)
			}
			mv_next_create(self.manager,
				_name,
				StageFinalScreen(name=_name,
					user=self.user,
					main_model=self.main_model,
					thematic_models=self.thematic_models,
					emotion_models=self.emotion_models,
					state=current_state))
			#final: write data to db (and forward)
			self.user.write(self._txt_poem.text, v_param = "self edit", forward = True)
			self.user.write_file_stage_end(stage_name, self._txt_poem.text, "FINAL")

		else:
			log ("MOVEBACK: unsupported origin:" + self.origin)
