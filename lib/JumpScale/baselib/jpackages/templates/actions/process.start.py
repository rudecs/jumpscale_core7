def main(j,jp):
   
    #start the application (only relevant for server apps)
    jp.log("start $(jp.name)")
    

    j.tools.startupmanager.startJPackage(jp)
    jp.waitUp(timeout=20)



    ####THIS IS ONLY EXAMPLE CODE FOR SPECIAL USECASES
    ##IF USAGE OF TMUX
    #cwd is working dir
    #j.system.platform.screen.executeInScreen("$jp_domain","$jp_name__$jp_instance",cmd,cwd="$base/apps/osis", env={},user="root")


    # if j.application.config.getBool("docker.enabled"):
    #     cmd=""
    #     j.system.process.execute(cmd)

