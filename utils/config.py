#!/usr/bin/env python
#coding=utf-8

from kivy.config import Config
import os

#CONFIGURATION FILE - BE CAREFUL WITH CHANGE COMMITED TO GIT!

#graphics: production layout. If True, full-screen, no cursor, no resize.
#Deactivate for any desktop / dev / debug usage.

#models: if True models are loaded and used for generation.
#Deactivate for speed-up starting and no generation (fake text), for UI tests.

#database: If True, ID is retriedved from, and data is saved to, mysql database (must be configured first)
#False: stand-alone installation, no DB required (ID: AUTO-TEST)
#TODO: currently no other logging method if False.

#print: send final result to printer

#web: send final result to web server

__production = False
if (__production): #don't touch anything here
	prod_graphics = True
	prod_models = True
	prod_database = False
	prod_print = True
	prod_web = True
	prod_log_terminal = True
	prod_showroom_print = False
else: #activate here the one you want or not
	prod_graphics = False
	prod_models = True
	prod_database = False
	prod_print = False
	prod_web = False
	prod_log_terminal = True
	prod_showroom_print = False

#Kivy Config: see documentation on https://kivy.org/doc/stable/api-kivy.config.html
#Warning: this affect ALL kivy apps (within the same installation, no worry if you have conda env containerized)

if (prod_graphics):
	Config.set('graphics', 'fullscreen', 'auto')
	Config.set('graphics', 'show_cursor', 0)
	Config.set('graphics', 'borderless', 1)
	Config.set('graphics', 'resizable', 0)
else:
	Config.set('graphics', 'fullscreen', 0)
	Config.set('graphics', 'height', 1000)
	Config.set('graphics', 'width', 1800)
	Config.set('graphics', 'show_cursor', 1)
	Config.set('graphics', 'borderless', 0)
	Config.set('graphics', 'resizable', 1)

Config.set('kivy', 'desktop', 1) #enable drag-able scroll-bar in scroll views
Config.set('kivy', 'exit_on_escape', 1)
Config.set('kivy', 'keyboard_mode', 'systemanddock') #allows both virtual and physical keyboards
Config.set('graphics', 'allow_screensaver', 0)

#KEYBOARD
Config.set('kivy', 'keyboard_layout', 'fr_CH') #alt: qwertz, querty, azerty, en_US, de_CH
#ISSUE1: @,tab,$ and / and all digits are available but not printable
#ISSUE2: many french special chars are not available (like ê, ç, œ, ï, etc)

Config.write()

#Models used in generation and adaptation of poems
MAIN_MODEL = ['gpt2-poetry-model-crpo']
THEMATIC_ROBERTA_MODELS = ['love', 'art', 'nature', 'religion', 'life']
EMOTION_ROBERTA_MODELS = ['happiness', 'sadness', 'anger']

THEMATIC_MODELS = ['amour_classified',  # deprecated in the English version
                   'art_classified', 
                   'nature_classified', 
                   'spiritualite_classified', 
                   'vie & mort_classified']
EMOTION_MODELS = ['joie_classified', 'tristesse_classified', 'aversion_classified']


# -1 for CPU, 0 to n for CUDA devices (like a NIVDIA GPU)
DEVICE = -1

#Path of the files
#home = str(Path.home()) # should work on linux and windows TODO: test on windows
#cpao_root = home + '/workspace/cpao'

#Teo : version that works on my windows system for messy testing
#home = 'E:/cpao'
#cpao_root = home + '/cpao'

# Andrei
home = os.path.expanduser('~')
cpao_root = os.path.join(home, 'crpo')

MODELS_GENERAL_PATH = os.path.join(cpao_root, 'models')
MODELS_ROB_PATH = os.path.join(cpao_root, 'models')
OUTPUT_DIRECTORY_FILE = os.path.join(cpao_root, 'logs')
RIME_PICKLE_FILE = os.path.join(cpao_root, 'utils/data', 'rhyming_dictionaries.pickle')
EMOTIONS_WORDS_LIST_FILE = os.path.join(cpao_root, 'utils/data', 'emotion_word_list.txt')
EMOTIONS_ASSOCIATIONS_FILE = os.path.join(cpao_root, 'utils/data', 'word_emotion_associations_english.npy')
THEMES_WORDS_LIST_FILE = os.path.join(cpao_root, 'utils/data', 'theme_word_list.txt')
THEMES_ASSOCIATIONS_FILE = os.path.join(cpao_root, 'utils/data', 'word_theme_associations_english.npy')

TEMPERATURE_GENERAL = 1.0
TEMPERATURE_THEMES = 0.15
TEMPERATURE_EMOTIONS = 0.15

ENDPOINT_MAC_MINI = "http://172.16.1.42:3000/api/poem"
ENDPOINT_DL2020_BACKEND = "https://dl2020.iict.ch/poemes"
#printer
TIMEOUT_LOCAL = 1
#web external
TIMEOUT_EXTERNAL = 3.05

from kivy.core.text import LabelBase

# registering fonts, as suggested by
# http://cheparev.com/kivy-connecting-font/
# https://github.com/eviltnan/kivy-font-example
KIVY_FONTS = [
	{
        "name": "Roboto", #default anyway
        "fn_regular": "utils/fonts/Roboto/Roboto-Regular.ttf",
        "fn_bold": "utils/fonts/Roboto/Roboto-Bold.ttf",
        "fn_italic": "utils/fonts/Roboto/Roboto-Italic.ttf",
        "fn_bolditalic": "utils/fonts/Roboto/Roboto-BoldItalic.ttf",
    },
    {
        "name": "RobotoCondensed",
        "fn_regular": "utils/fonts/Roboto/Roboto-Light.ttf",
        "fn_bold": "utils/fonts/Roboto/Roboto-Medium.ttf",
        "fn_italic": "utils/fonts/Roboto/Roboto-LightItalic.ttf",
        "fn_bolditalic": "utils/fonts/Roboto/Roboto-MediumItalic.ttf",
    }
]

# for registering custom fonts
for font in KIVY_FONTS:
    LabelBase.register(**font)
