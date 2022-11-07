import utils.config as conf
import os
if conf.prod_database:
	from db.db_internal import DB #needs mysql.connector to be installed

from datetime import datetime, timezone

# This class allows a user to "login" with its id_card, to stay authenticated and write information.
# No data retrieval is possible because its single session usage.

class User (object):
	
	__id_card = "KEINE" # 5 position key ensures this is impossible to reach
	__stage = 0
	_max_stage = 3
	_prod_db = False
		
	def check_default (self):
		return self.__id_card == "KEINE"
	
	def __init__(self):
		pass
		
	def login_auto(self, prod_database = True):
		self._prod_db = prod_database
		if prod_database:
			db = DB()
			self.__id_card = db.id_get_any_valid()
			db.cnx_logout()
		else:
			self.__id_card = "AUTO-TEST"
			#TODO: give a local ID without database
		self.__stage = 1
		return self.__id_card
		
	def getID(self):
		return self.__id_card
		
	#Unified format for current time (similar in file names, and timestamp in logs)
	#ISO formats: YYYY-mm-ddTHH:MM:SS[+00:00]
	#File format: YYYY-mm-dd_HH-MM-SS (Windows compatibility: no space and no semi-colon :)
	def now_internal_json(self):
		#Switzerland is UTC+1 in CET Central European Time; UTC+2 in CEST Summer Time (daylight saving)
		dt = datetime.now(tz=timezone.utc)
		ts = dt.timestamp() #POSIX
		dt_iso = dt.isoformat(sep = '_', timespec='seconds')
		return "\t\t\"datetime\": \"" + dt_iso + "\",\n" + "\t\t\"timestamp\": \"" + str(ts) + "\",\n"
		
	def now_internal_file(self):
		return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
	
	def poem_internal_format(self, poem):
		return poem.replace("\n", "\\n")

	# Allow to know when a user actually logged in (may be very long after acquiring ID)
	# Creates the logs file for the "user" and keep its reference until this User object is not used anymore
	def start_auto(self):
		# outfile_directory = conf.OUTPUT_DIRECTORY_FILE
		now = self.now_internal_file()
		now_json = self.now_internal_json()
		# self.out_file = outfile_directory + now + "_" + self.__id_card + '.json'
		self.out_file = os.path.join(conf.OUTPUT_DIRECTORY_FILE, now + '.json')
		
		with open(self.out_file, 'w') as f:
			f.write("{" + "\n")
			f.write(now_json)
			f.write("\"id\": \"" + self.__id_card+ "\", \n")
			##f.write("\"two_lines\": \"Hello, \\nWorld!\", \n") #\n need TWO escapes!
			f.write("\"stages\": [\n") #Array of stages started
			f.write("[],\n") #Mock array (stage "0" in JSON numbering)
			f.write("[\n") #Array stage 1 started
			
        #TODO: DB-DEPRECATED
		if self._prod_db:
			db = DB ()
			r = db.id_started(self.__id_card)
			db.cnx_logout()
			return r
		else:
			return False
		
	# Logins a user with given ID. Usable only once per valid ID.
	# Returns true if succesfully logged and User object has now id_card set => can perform write
	# Returns false if id_card is non-existent (absent), or already used (non-blank)
	
	# DEPRECATED
	def login(self,id_card):
		if self._prod_db:
			db = DB()
			r = False
			#Non-existent entry // Non-blank entry // internal login
			if db.id_exists(id_card) and db.id_blank(id_card) and db.id_working(id_card):
				r = True
				self.__id_card = id_card
				self.__stage = 1
				#unsupported pre-stage, goes directly to stage 1
			db.cnx_logout()
			return r
		else:
			return False


	# Write the START (beginning) or RESTART (after cancelation of edition) of a stage with the current poem version (from N-1 stage, if N=0 poem is empty string and this only logs the beginning of times)
	# This message is triggered when a new stage is started (AND also when a user clicks cancel from edition screen and the stage reloads the last known version, created from backend).
	#empty poem arise at very beginning when there is no poem yet, and also at typography intermediate steps (text does not change, only user params for fonts)
	def write_file_stage_start (self, stage, poem):
		with open(self.out_file, 'a', encoding = "utf-8") as f:
			f.write("\t{\n")
			f.write("\t\t\"stage\": \"" + stage + "\",\n")
			f.write("\t\t\"state\": \"start\",\n")
			f.write(self.now_internal_json())
			f.write("\t\t\"params\": \"\", \n") #No params for start state
			f.write("\t\t\"poem\": \"")
			f.write(self.poem_internal_format(poem))
			f.write("\"\n")
			f.write("\t},\n")

	# Write some and many intermediate stages of the user interaction
	# v_param is the stage params
	# everytime the back-end is triggered, it records the results: by clicking generate (#1) / adapt themes & emotions (#2 & #3) / suggest rhyme (#4) / get a suggested typography (#5)
	# (also records the discarded draft (eventually modified or not) when cancelling edition)
	#This message is triggered every time a user gets something from back-end (with the params used), AND also the discarded draft when cancel edition ([self-edit-back-cancel]).
	def write_file_stage_interm (self, stage, poem, v_param = ""):
		with open(self.out_file, 'a', encoding = "utf-8") as f:
			f.write("\t{\n")
			f.write("\t\t\"stage\": \"" + stage + "\",\n")
			f.write("\t\t\"state\": \"interm\",\n")
			f.write(self.now_internal_json())
			f.write("\t\t\"params\": \"")
			f.write(v_param)
			f.write("\",\n")
			
			f.write("\t\t\"poem\": \"")
			f.write(self.poem_internal_format(poem))
			f.write("\"\n")
			f.write("\t},\n")

	# Write the very END of a stage with the last known poem version (user modified or not is stored the key parameter)
	# key can be "NEXT-STAGE" or "NEXT-EDIT", or "FINAL" when this is the very last entry (from the #5 typography next button)
	# This message is triggered when user clicks NEXT (either on proper stage, either on edition screen) and moves definitevely to the next stage of the application.\n")
	def write_file_stage_end (self, stage, poem, key):
		with open(self.out_file, 'a', encoding = "utf-8") as f:
			f.write("\t{\n")
			f.write("\t\t\"stage\": \"" + stage + "\",\n")
			f.write("\t\t\"state\": \"final\",\n")
			f.write(self.now_internal_json())
			f.write("\t\t\"params\": \"")
			f.write(key)
			f.write("\",\n")
			
			f.write("\t\t\"poem\": \"")
			f.write(self.poem_internal_format(poem))
			f.write("\"\n")
			f.write("\t}\n")
			
			#extra bracket at the end for next stage or finalize
			if ("FINAL" != key) : #close the current stage and open the next one
				f.write("],\n")
				f.write("[\n")
			else: 
				f.write("]\n") #close the current (last) stage
				f.write("],\n") #Array of stages closed
				f.write("\"poem_final\": \"" + self.poem_internal_format(poem) + "\"\n") #closes stages
				f.write("}\n") #closes file


	#TODO: DB-DEPRECATED
	def write(self, poem, v_param = "", forward = True):
		if self._prod_db:
			if self.check_default(): return False
			if (self.__stage > self._max_stage) : return False
			db = DB()
			r = db.id_write(self.__id_card, self.__stage, poem, v_param)
			if (r and forward): #automatic forward and finish
				self.__stage += 1
				if (self.__stage > self._max_stage) :
					r = db.id_finish(self.__id_card, False) # finish without timeout
					#TODO: step design / font is not yet supported
			db.cnx_logout()
			return r
		else:
			return False
		
	def read(self):
		if self._prod_db:
			goal = self.__stage - 1
			if goal < 1 : return False # reject -1 and 0 (pre-stage) properly
			db = DB()
			r = db.id_read(self.__id_card, self.__stage - 1)
			db.cnx_logout()
			return r
		else:
			return "NO DATA"
	
	def timeout(self):
		if self._prod_db:
			db = DB()
			r = db.id_finish(self.__id_card, True) # finish with timeout
			db.cnx_logout()
			return r
		else:
			return False
