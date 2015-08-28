
help="""session.list"""
description=help

def action(handler,tg,message):
    session=handler.checkSession(tg,message,name="test",newcom=True)    
    m="\n".join(["- %s"%item for item in handler.sessions.keys() ])
    session.send_message(m)
