from JumpScale import j

from Telegram import Telegram

from handlers.loggerHandler import LoggerHandler
from handlers.DemoHandler import DemoHandler


class TelegramBot:
    """
    """

    def __init__(self,telegramkey=None):
        """
        @param key eg. 112456445:AAFgQVEWPGztQc1S8NW0NXY8rqQLDPx0knM
        """
        print "key:%s"%telegramkey

        self.api=Telegram("https://api.telegram.org/bot",telegramkey)

    def addLogHandler(self,path="/tmp/chat.log"):
        """
        loggerHandler = LoggerHandler("chat.log")
        self.api.add_handler(loggerHandler)
        """
        loggerHandler = LoggerHandler(path)
        self.api.add_handler(loggerHandler)

    def addDemoHandler(self):
        """        
        """
        handler = DemoHandler()
        self.api.add_handler(handler)

    def addHandler(self,handler):
        """
        handler = OurHandler()
        telegrambot.addHandler(handler)
        """
        self.api.add_handler(handler)


    def start(self):
        self.api.process_updates()


