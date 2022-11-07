from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.clock import Clock

from utils.utils import log, mv_back, mv_next, mv_next_create
from frontend.stage_4_rhyme import StageRhymeScreen
from frontend.stage_manual_edition import StageManualEditionScreen

import utils.config as conf
if (conf.prod_models):
	from backend.adapt_with_models import adapt_poem_with_models

with open('frontend/widgets.kv', encoding='utf8') as f:
	Builder.load_string(f.read())
with open('frontend/screen_3_emotion.kv', encoding='utf8') as f:
	Builder.load_string(f.read())

stage_name = "3.0-THREE-EMOTION"
#STAGE THREE (3.0)
#Emotions fitting stage
class StageEmotionScreen(Screen):
	params = ""
	txt_intro = "Choose one or more emotions that I will use \n to adapt the poem."
	txt_wait = "Adapting the poem: please wait.\nI am busy with complex calculations."
	txt_wait_poem = "Creation in progress..."
	txt_result = "Here is my proposal: it may not be perfect,\nso feel free to edit it as you like."

	def __init__(self, user, main_model, thematic_models, emotion_models, state, **kwargs):
		super(StageEmotionScreen, self).__init__(**kwargs)
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
		self._thm_sld1.value = state.get("sld1_value", 30)
		self._thm_sld2.value = state.get("sld2_value", 0)
		self._thm_sld3.value = state.get("sld3_value", 0)
		self.update_emotions_tuple()

		self.user.write_file_stage_start(stage_name, self._adapted_poem)

	def _notify_change_settings(self):
		self._btn_adapt.disabled = False
		self.update_emotions_tuple()

	def btn_adapt_press(self, btn):
		btn.disabled = True
		self._btn_edit.disabled = True
		self._btn_next.disabled = True
		self.ui_able()

		self._main_txt.text = self.txt_wait
		self._txt_poem.text = self.txt_wait_poem

	def btn_adapt_release(self, btn):
		Clock.schedule_once(self.adapt, 0.1)

	def ui_able(self, disabled = True):
		self._thm_sld1.disabled = disabled
		self._thm_sld2.disabled = disabled
		self._thm_sld3.disabled = disabled
		#TODO: eventl set grey the slider labels ?

	def update_emotions_tuple(self):
		self.emo_tuple = (int(self._thm_sld1.value), int(self._thm_sld2.value), int(self._thm_sld3.value))

	def sld_change(self, slider):
		self._notify_change_settings()
		return True

	def adapt(self, dt):
		self.params = '['+ str(int(self._thm_sld1.value)) + ',' + \
						   str(int(self._thm_sld2.value)) + ',' + \
						   str(int(self._thm_sld3.value)) + ']'
		result = ()
		if (conf.prod_models):
			result = adapt_poem_with_models(poem=self._base_poem,
				models=self.emotion_models,
				associations_file_path=conf.EMOTIONS_ASSOCIATIONS_FILE,
				word_list_path=conf.EMOTIONS_WORDS_LIST_FILE,
				mixing_numbers=self.params,
				temperature=conf.TEMPERATURE_EMOTIONS,
				debug=False,
				roberta_models=self.emotion_models)
		else: #fake texts for faster tests only
			text = self._base_poem \
			+ "\nStage THREE 3.0 : Emotions" \
			+ "\n Joie:" + str(int(self._thm_sld1.value)) \
			+ "\n Tristesse:" + str(int(self._thm_sld2.value)) \
			#+ "\n Aversion:" + str(int(self._thm_sld3.value)) #children-friendly version:
			+ "\n Haine:" + str(int(self._thm_sld3.value))
			result = (text, text)

		self._btn_adapt.disabled = False
		self._btn_edit.disabled = False
		self._btn_next.disabled = False
		self.ui_able(disabled = False)

		self._txt_poem.text = result[0]
		self._adapted_poem = result[1]
		self._main_txt.text = self.txt_result
		self._btn_adapt.text = "Readapt your poem"

		# write the intermediate result from back-end
		self.user.write_file_stage_interm(stage_name, self._adapted_poem, v_param = self.params)

		#TODO : DB-DEPRECATED
		#saves the draft data to db (without forward)
		self.user.write(self._adapted_poem, v_param = self.params, forward = False)

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
			"sld1_value": self._thm_sld1.value,
			"sld2_value": self._thm_sld2.value,
			"sld3_value": self._thm_sld3.value,
			"params": self.emo_tuple,
			"origin": 3
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

		#Write the current version as definitive.
		self.user.write_file_stage_end(stage_name, self._adapted_poem, "NEXT-STAGE")

		#TODO : DB-DEPRECATED
		#write data to db (and forward)
		self.user.write(self._adapted_poem, v_param = self.params, forward = True)

		#move forward to next stage
		_name = "StageRhymeScreen"
		current_state = {
			"poem": self._adapted_poem,
			"joie_value": self._thm_sld1.value,
			"tristesse_value": self._thm_sld2.value,
			"aversion_value": self._thm_sld3.value
		}
		mv_next_create(self.manager,
			_name,
			StageRhymeScreen(name=_name,
				user=self.user,
				main_model=self.main_model,
				thematic_models=self.thematic_models,
				emotion_models=self.emotion_models,
				state=current_state))
