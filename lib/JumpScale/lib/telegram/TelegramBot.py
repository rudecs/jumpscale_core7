from JumpScale import j

from Telegram import Telegram

from handlers.loggerHandler import LoggerHandler
from handlers.DemoHandler import DemoHandler
from handlers.InteractiveHandler import InteractiveHandler

import gevent

class TelegramBot:
    """
    """

    def __init__(self,telegramkey=None):
        """
        @param key eg. 112456445:AAFgQVEWPGztQc1S8NW0NXY8rqQLDPx0knM
        """
        print "key:%s"%telegramkey

        self.api=Telegram("https://api.telegram.org/bot",telegramkey)        

    # def addLogHandler(self,path="/tmp/chat.log"):
    #     """
    #     loggerHandler = LoggerHandler("chat.log")
    #     self.api.add_handler(loggerHandler)
    #     """
    #     loggerHandler = LoggerHandler(path)
    #     self.api.add_handler(loggerHandler)


    def addDemoHandler(self):
        """        
        """
        handler = DemoHandler()
        self.api.add_handler(handler)

    def addCustomHandler(self,handler):
        """
        handler = OurHandler()
        telegrambot.addHandler(handler)
        """
        self.api.add_handler(handler)

    def start(self):
        """
        will always look for actions in subdir 'actions'
        each name of script corresponds to name of action
        """
        # self.api.process_updates()
        h=InteractiveHandler()
        h.maintenance()
        self.api.add_handler(h)
        gevent.spawn(self.api.process_updates)
        while True:
            gevent.sleep(1)
            for handler in self.api.handlers:
                handler.maintenance()

