# coding=utf-8
from __future__ import absolute_import
from .discord import Hook, InfoTracker

import json
import octoprint.plugin
import octoprint.settings
import requests
from datetime import timedelta
from PIL import Image
from io import BytesIO
import subprocess
import os

class OctorantPlugin(octoprint.plugin.EventHandlerPlugin,
					 octoprint.plugin.StartupPlugin,
					 octoprint.plugin.SettingsPlugin,
                     octoprint.plugin.AssetPlugin,
                     octoprint.plugin.TemplatePlugin,
					 octoprint.plugin.ProgressPlugin):

	def __init__(self):
		# Events definition here (better for intellisense in IDE)
		# referenced in the settings too.
		self.events = {
			"startup" : {
				"name" : "Octoprint Startup",
				"enabled" : True,
				"with_snapshot": False,
				"message" : "Startup  - default"
			},
			"shutdown" : {
				"name" : "Octoprint Shutdown",
				"enabled" : False,
				"with_snapshot": False,
				"message" : "Shutdown - default"
			},
			"printer_state_operational":{
				"name" : "Printer state : operational",
				"enabled" : False,
				"with_snapshot": False,
				"message" : "Operational - default"
			},
			"printer_state_error":{
				"name" : "Printer state : error",
				"enabled" : True,
				"with_snapshot": False,
				"message" : "Error - default"
			},
			"printer_state_unknown":{
				"name" : "Printer state : unknown",
				"enabled" : True,
				"with_snapshot": False,
				"message" : "Unknown state - default."
			},
			"printing_started":{
				"name" : "Printing process : started",
				"enabled" : True,
				"with_snapshot": True,
				"message" : "Starting a print - default"
			},
			"printing_paused":{
				"name" : "Printing process : paused",
				"enabled" : True,
				"with_snapshot": True,
				"message" : "Paused - default"
			},
			"printing_resumed":{
				"name" : "Printing process : resumed",
				"enabled" : True,
				"with_snapshot": True,
				"message" : "Resumed - default"
			},
			"printing_cancelled":{
				"name" : "Printing process : cancelled",
				"enabled" : True,
				"with_snapshot": True,
				"message" : "Cancelled - default"
			},
			"printing_done":{
				"name" : "Printing process : done",
				"enabled" : True,
				"with_snapshot": True,
				"message" : "Done - default"
			},
			"printing_failed":{
				"name" : "Printing process : failed",
				"enabled" : True,
				"with_snapshot": True,
				"message" : "Failed - default"
			},
			"printing_progress":{
				"name" : "Printing progress",
				"enabled" : True,
				"with_snapshot": True,
				"message" : "Printing  - default",
				"step" : 10
			},
			"test":{ # Not a real message, but we will treat it as one
				"enabled" : True,
				"with_snapshot": True,
				"message" : "Testing setting.. see this? then it worked.."
			},
		}
		self.__InfoTracker = InfoTracker()
		self.__discordCall = Hook()

		
	def on_after_startup(self):
		self._logger.info("Octorant is started !")


	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return {
			'url': "https://discordapp.com/api/webhooks/696566735163359262/vk2w_6JWMU7j_Pl6Nlf2atdihP3cuQT6laZe_K0IOZIsWt8B6Bxavfg_SdSfwEJeGq-r",
			'username': "",
			'avatar': "",
			'side_bar': "FFFFFF",
			'events' : self.events,
			'allow_scripts': False,
			'script_before': '',
			'script_after': ''
		}

	# Restricts some paths to some roles only
	def get_settings_restricted_paths(self):
		# settings.events.tests is a false message, so we should never see it as configurable.
		# settings.url, username and avatar are admin only.
		return dict(never=[["events","test"]],
					admin=[["url"],["username"],["avatar"],["side_bar"],['script_before'],['script_after']])

	##~~ AssetPlugin mixin

	def get_assets(self):
		#self._logger.info("get_assets()")
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/octorant.js"],
			css=["css/octorant.css"]
		)


	##~~ TemplatePlugin mixin
	def get_template_configs(self):
		#self._logger.info("get_template_configs()")
		return [
			dict(type="settings", custom_bindings=False)
		]

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			octorant=dict(
				displayName="Octorant Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="bchanudet",
				repo="OctoPrint-Octorant",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/bchanudet/OctoPrint-Octorant/archive/{target_version}.zip"
			)
		)

	##~~ EventHandlerPlugin hook

	def on_event(self, event, payload):
		#self._logger.info("on_event({}): {}".format(event, payload))

		if event == "ZChange":
			self.__InfoTracker.setZ(payload["new"])
		elif event == "Startup":
			self.__discordCall.init(self._settings.get(["url"], merged=True),
									self._settings.get(["username"],merged=True),
									self._settings.get(['avatar'],merged=True),
									self._settings.get(['side_bar'],merged=True) )
			return self.notify_event("startup")
		elif event == "Shutdown":
			self.__InfoTracker.clear()
			return self.notify_event("shutdown")
		elif event == "PrinterStateChanged":
			if payload["state_id"] == "OPERATIONAL":
				return self.notify_event("printer_state_operational")
			elif payload["state_id"] == "ERROR":
				return self.notify_event("printer_state_error")
			elif payload["state_id"] == "UNKNOWN":
				return self.notify_event("printer_state_unknown")
		elif event == "PrintStarted":
			return self.notify_event("printing_started",payload)	
		elif event == "PrintPaused":
			return self.notify_event("printing_paused",payload)
		elif event == "PrintResumed":
			return self.notify_event("printing_resumed",payload)
		elif event == "PrintCancelled":
			return self.notify_event("printing_cancelled",payload)
		elif event == "PrintDone":
			payload['time_formatted'] = str(timedelta(seconds=int(payload["time"])))
			return self.notify_event("printing_done", payload)
	
		return True

	def on_print_progress(self,location,path,progress):
		self.notify_event("printing_progress",{"progress": progress})

	def on_settings_save(self, data):
		old_bot_settings = '{}{}{}{}'.format(\
			self._settings.get(['url'],merged=True),\
			self._settings.get(['avatar'],merged=True),\
			self._settings.get(['username'],merged=True),\
			self._settings.get(['side_bar'],merged=True)\
		)
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		new_bot_settings = '{}{}{}{}'.format(\
			self._settings.get(['url'],merged=True),\
			self._settings.get(['avatar'],merged=True),\
			self._settings.get(['username'],merged=True),\
			self._settings.get(['side_bar'],merged=True)\
		)
	
		if(old_bot_settings != new_bot_settings):
			self._logger.info("Settings have changed. Send a test message...")
			self.notify_event("test")


	def notify_event(self,eventID,data={}):
		if(eventID not in self.events):
			self._logger.error("Tried to notifiy on inexistant eventID : ", eventID)
			return False
		#self._logger.info("notify_event({}, {}): start".format(eventID, data))
		
		tmpConfig = self._settings.get(["events", eventID],merged=True)
		if tmpConfig["enabled"] != True:
			self._logger.debug("Event {} is not enabled. Returning gracefully".format(eventID))
			return False

		self.__InfoTracker.printerData(self._printer.get_current_data())

		# Uptade tracker with current state
		if eventID == 'printing_started':
			self.__InfoTracker.start(data['name'], data['size'])
		elif eventID == "printing_cancelled":
			self.__InfoTracker.stop(data['time'])
		elif eventID == 'printing_done':
			self.__InfoTracker.stop()
		elif eventID in ['shutdown', 'startup']:
			self.__InfoTracker.clear()

		# Special case for progress eventID : we check for progress and steps
		elif eventID == 'printing_progress':
			self.__InfoTracker.progress(data["progress"], tmpConfig["step"])
			if (int(tmpConfig["step"]) == 0 \
				or int(data["progress"]) == 0 \
				or int(data["progress"]) % int(tmpConfig["step"]) != 0 \
				or (int(data["progress"]) == 100) \
			) :
				return False

		return self.send_message(eventID, tmpConfig["message"], tmpConfig["with_snapshot"])

	def exec_script(self, eventName, which=""):

		# I want to be sure that the scripts are allowed by the special configuration flag
		scripts_allowed = self._settings.get(["allow_scripts"],merged=True)
		if scripts_allowed is None or scripts_allowed == False:
			return ""

		# Finding which one should be used.
		script_to_exec = None
		if which == "before":
			script_to_exec = self._settings.get(["script_before"], merged=True)
		
		elif which == "after":
			script_to_exec = self._settings.get(["script_after"], merged=True)
		
		# Finally exec the script
		out = ""
		self._logger.debug("{}:{} File to start: '{}'".format(eventName, which, script_to_exec))

		try:
			if script_to_exec is not None and len(script_to_exec) > 0 and os.path.exists(script_to_exec):
				out = subprocess.check_output(script_to_exec)
		except (OSError, subprocess.CalledProcessError) as err:
				out = err
		finally:
			self._logger.debug("{}:{} > Output: '{}'".format(eventName, which, out))
			return out


	def send_message(self, eventID, message, withSnapshot=False):
		# return false if no URL is provided
		if "http" not in self._settings.get(["url"],merged=True):
			return False

		# exec "before" script if any
		self.exec_script(eventID, "before")
		
		# Get snapshot if asked for
		snapshot = None
		snapshotUrl = self._settings.global_get(["webcam","snapshot"])
		if 	withSnapshot and snapshotUrl is not None and "http" in snapshotUrl :
			try:
				snapshotCall = requests.get(snapshotUrl)

				# Get the settings used for streaming to know if we should transform the snapshot
				mustFlipH = self._settings.global_get_boolean(["webcam","flipH"])
				mustFlipV = self._settings.global_get_boolean(["webcam","flipV"])
				mustRotate = self._settings.global_get_boolean(["webcam","rotate90"])

				# Only do something if we got the snapshot
				if snapshotCall :
					snapshotImage = BytesIO(snapshotCall.content)				

					# Only call Pillow if we need to transpose anything
					if (mustFlipH or mustFlipV or mustRotate): 
						img = Image.open(snapshotImage)

						self._logger.info("Transformations : FlipH={}, FlipV={} Rotate={}".format(mustFlipH, mustFlipV, mustRotate))

						if mustFlipH:
							img = img.transpose(Image.FLIP_LEFT_RIGHT)
						
						if mustFlipV:
							img = img.transpose(Image.FLIP_TOP_BOTTOM)

						if mustRotate:
							img = img.transpose(Image.ROTATE_90)

						newImage = BytesIO()
						img.save(newImage,'png')			

						snapshotImage = newImage	

					snapshot = {'file': ("snapshot.png", snapshotImage.getvalue())}
			except requests.ConnectionError:
				snapshot = None
				self._logger.error("{}: ConnectionError on: '{}'".format(eventID, snapshotUrl))
			except requests.ConnectTimeout:
				snapshot = None
				self._logger.error("{}: ConnectTimeout on: '{}'".format(eventID, snapshotUrl))

		# Send to Discord WebHook
		out = self.__discordCall.post(message, snapshot, self.__InfoTracker.data)

		# exec "after" script if any
		self.exec_script(eventID, "after")

		return out
		
# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "OctoRant"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = OctorantPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

