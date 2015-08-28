
help="""

Available Commands
- menu        : print menu of things to do depending context you are in
- test.start  : will ask which test to start & will execute
- test.define : will define a test
- test.list   : will list your tests
- grafanaconf : configure grafana connection (to gather statistics) (EXPERT)

cmds in test context
- cpu   : show cpu stats
- io    : show io stats

"""
description="do a test thing"

def action(handler,tg,message):
    print "test.define"
    markup={}

    session=handler.checkSession(tg,message,name="test",newcom=True)      
    result=int(session.send_message("Please specify how many VNAS'es you would like to use (1-10).",True))
    for i in range(result):
        session.send_message(str(i))
    markup=[["Yes"],["No"]]
    result=session.send_message("Do you want custom settings?",True,markup=markup)
    session.stop_communication()
    
    # tg.send(send_message.chat.id, "Please specify how many VNAS'es you would like to use (1-10).",reply_to_message_id="", reply_markup="")
    # markup={}
    # markup["nr of vnas to use"]=[["1"],["2"],["3"],["1"],["2"],["3"],["1"],["2"],["3"]]
    # markup["resize_keyboard"]=True
    # markup["one_time_keyboard"]=True      