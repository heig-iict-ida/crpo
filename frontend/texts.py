#!/usr/bin/python
# coding=utf-8

# language & internationalization management
# change current to change future texts callings
class lang:
	no = -1
	en = 1
	fr = 2
	default = fr
	current = default

class Text:
	def __init__(self, en="(missing)", fr="(manquant)"):
		self.english = en
		self.french = fr

	def get(self, l=lang.no):
		if (lang.no == l):
			l = lang.current
		switch = {
			lang.en: self.english,
			lang.fr: self.french
		}
		return switch.get(l)

txt_wel_title = Text(
	en="-",
	fr="Welcome to CRPO!\n\nAn AI-based assistant\nfor poem creation"
	)

txt_wel_btn_connect = Text(
	en="-",
	fr="Start creating a poem"
	)
