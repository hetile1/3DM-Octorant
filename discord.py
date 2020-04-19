#coding: utf-8

# Simple module to send messages through a Discord WebHook

import json
import requests
import time
from datetime import timedelta
from discord_webhook import DiscordWebhook, DiscordEmbed

class InfoTracker():
    def __init__(self):
        self.bootTime	= time.time()
        self.startTime	= time.time()
        self.totalTime  = False
        self.data		= {}
        self.size       = 0
        self.pos        = 0

    def _getTime(self, thisTime):
        return str(timedelta(seconds=int(thisTime)))

    def start(self, fileName, size):
        self.data.clear()
        self.totalTime      = False
        self.startTime		= time.time()
        self.data['file']	= str(fileName).replace('.gcode', '').replace('.GCODE', '')
        self.size           = float(size) / 1048576
        self.filePos(0)

    def done(self):
        for i in ["step", "progress", "filePos", "printTimeLeft"]:
            try:
                del self.data[i]
            except:
                pass

    def stop(self, stopTime=False):
        if stopTime:
            self.data["time"] = self._getTime(stopTime)
        try:
            del self.data["printTimeLeft"]
        except:
            pass

    def clear(self):
        self.data.clear()

    def printTimeLeft(self, printTimeLeft):
        if int(printTimeLeft) > 10:
            if not self.totalTime:
                self.data["totalTime"] = self._getTime(printTimeLeft)
                self.totalTime = True
            else:
                self.data['printTimeLeft'] = self._getTime(printTimeLeft)
        else:
            try:
                del self.data['printTimeLeft']
            except:
                pass

    def printTime(self, printTime):
        if int(printTime) > 0:
            self.data['printTime'] = self._getTime(printTime)

    def filePos(self, filePos):
        self.pos    = float(filePos) / 1048576
        self.data["printed"] = "{:.2f} / {:.2f}MB".format(self.pos, self.size)

    def printerData(self, ddata):
        if ddata["progress"] is not None:
            if ddata["progress"]["printTimeLeft"] is not None:
                self.printTimeLeft(ddata["progress"]["printTimeLeft"])
            if ddata["progress"]["printTime"] is not None:
                self.printTime(ddata["progress"]["printTime"])
            if ddata["progress"]["filepos"] is not None:
                self.filePos(ddata["progress"]["filepos"])

    def setZ(self, z):
        if "currentZ" in self.data:
            if z > self.data["currentZ"]:
                self.data["currentZ"] = z
        else:
            self.data["currentZ"] = z

    def progress(self, progress, step):
        if int(progress) > 0:
            self.data["progress"]	= "{0}% _(step:{1})_".format(progress, step)


class Hook():
    def __init__(self):
        self.urls = []
        self.username = "username"
        self.avatar = "avatar"
        self.side_bar = 0x000000

    def init(self, url, username="", avatar="", side_bar="a21d1d"):
        self.urls = url.replace(' ', '').split(',')
        self.username = username
        self.avatar = avatar
        self.side_bar = eval("0x" + side_bar.replace('#', '').rstrip())

    def post(self, message, attachment, data):

        webhook = DiscordWebhook(url=self.urls, username=self.username, avatar_url=self.avatar)
        embed = DiscordEmbed(title=message, color=self.side_bar)
        embed.set_footer(text='3DM-Octorant _beta 0.3.1_', icon_url="https://cdn.discordapp.com/emojis/673897582375993365.png")
        embed.set_timestamp()

        for k in data:
            if data[k] is not None:
                embed.add_embed_field(name=format(k), value=format(data[k]))

        if attachment is not None:
            webhook.add_file(file=attachment["file"][1], filename="0.png")
            embed.set_image(url='attachment://0.png')

        webhook.add_embed(embed)
        webhook.execute()
    
        return True
