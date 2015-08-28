
help="""session.list"""
description=help

def action(handler,tg,message):
    session=handler.checkSession(tg,message,name="session.list",newcom=True)    
    # m="\n".join(["- %s"%item for item in handler.sessions.keys() ])
    markup={}
    result=session.send_message("Please specify which session to delete.",True)
    markup=handler.sessions.keys()
    markup.sort()
    res=session.send_message("Do you want specify iozone custom arguments?",True,markup=markup)

    session.stop_communication()