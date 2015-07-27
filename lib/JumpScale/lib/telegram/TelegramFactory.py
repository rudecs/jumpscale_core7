from JumpScale import j

from TelegramBot import *
import os

class TelegramFactory:

    def get(self, telegramkey=""):
        """
        @param telegramkey eg. 112456445:AAFgQVEWPGztQc1S8NW0NXY8rqQLDPx0knM
        if not filled in will try to get from env variable: telegram
        set as follows: export telegram=1124...
        """

        if telegramkey=="":
            if not os.environ.has_key("telegram"):
                j.events.inputerror_critical("Cannot find env var telegram please in shell do: export telegram=1124...")
            telegramkey=os.environ["telegram"]

        return TelegramBot(telegramkey)

    def demo(self):
        """
        tg=self.get()
        tg.addDemoHandler()
        tg.start()
        """
        tg=self.get()
        tg.addDemoHandler()
        tg.start()

    def demoMS1(self):
        """
        instructions how to load a handler

        tg=j.tools.telegrambot.get()
        from handlers.DemoHandlerMS1 import *
        handler = DemoHandlerMS1()
        tg.api.add_handler(handler)
        tg.start()
        
        """
        tg=j.tools.telegrambot.get()
        from handlers.DemoHandlerMS1 import *
        handler = DemoHandlerMS1()
        tg.api.add_handler(handler)
        tg.start() 