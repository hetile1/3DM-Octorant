#coding: utf-8

# Simple module to send messages through a Discord WebHook

import json
import requests
from discord_webhook import DiscordWebhook, DiscordEmbed


class Hook():

    def __init__(self, url, message, username="", avatar="", side_bar="a21d1d", data=None, attachment=None):
        self.url = url
        self.message = message
        self.username = username
        self.avatar = avatar
        self.side_bar = eval("0x" + side_bar.replace('#', '').rstrip())
        self.data = data
        self.attachment = attachment
        self.payload = {}

    def format(self):
        self.payload = {
            'content': self.message,
            'username' : self.username,
            'avatar_url' : self.avatar
        }

    def post(self):
        self.format()

        urls = self.url.replace(' ', '').split(',')
        for myurl in urls:
            webhook = DiscordWebhook(url=myurl, username=self.username, avatar_url=self.avatar)
            embed = DiscordEmbed(title=self.message, color=self.side_bar)
            embed.set_footer(text='3DMeltdown-octorant _beta 0.2.5_', icon_url="https://cdn.discordapp.com/emojis/673897582375993365.png")
            embed.set_timestamp()

            for k in self.data:
                if self.data[k] is not None:
                    embed.add_embed_field(name=format(k), value=format(self.data[k]))

            if self.attachment is not None:
                webhook.add_file(file=self.attachment["file"][1], filename="0.png")
                embed.set_image(url='attachment://0.png')

            webhook.add_embed(embed)
            webhook.execute()

    
        return True

#        resp = requests.post(self.url,files=self.attachment,data=self.payload)
