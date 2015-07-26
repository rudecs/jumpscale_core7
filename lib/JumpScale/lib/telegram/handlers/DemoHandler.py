from datetime import datetime

import json
from JumpScale import j

class DemoHandler:

    def __init__(self):

        url="http://www.greenitglobe.com/gig/.files/img/logo.png"
        j.do.download(url,to="%s/giglogo.png"%j.dirs.tmpDir,overwrite=False)


        self.once=True

    def on_text(self, tg, message):
            
        # markup={}
        # markup["force_reply"]=True

        # tg.send_message(message.chat.id, "this is me",reply_to_message_id=None,reply_markup=json.dumps(markup))               

        if self.once==True:
            tg.send_message(message.chat.id, "Welcome to the demo bot")
            print "send init photo"
            tg.send_photo(message.chat.id, "%s/giglogo.png"%j.dirs.tmpDir,reply_to_message_id="", reply_markup="")
            print "photo send"
            self.once=False


        markup={}
        markup["keyboard"]=[["yes"],["no"],["1","2","3"],["stop"],["send photo"]]
        markup["resize_keyboard"]=True
        markup["one_time_keyboard"]=True

        if message.text=="send photo":
            tg.send_photo(message.chat.id, "%s/giglogo.png"%j.dirs.tmpDir,reply_to_message_id="", reply_markup="")

        if not message.text=="stop":

            tg.send_message(message.chat.id, "Please fill in",reply_to_message_id=None,reply_markup=json.dumps(markup))                    


        