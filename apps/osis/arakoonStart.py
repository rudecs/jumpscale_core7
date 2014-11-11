from JumpScale import j

j.application.start("arakoonstarttest")

if __name__ == '__main__':

	arakoonInstance = q.manage.servers.arakoon.new("anInstanceName")

	# the following needs to be done on each node
	arakoonInstance.clusterConfigSet("192.168.1.1:5000,192.168.1.2:5000,192.168.1.3:5000")  # means cluster with 3 on port 5000

	# REMARKS
	# no pylabs specific config files are created, only config files directly from arakoon

	arakoonInstance.clusterConfigGet()  # returns something like "192.168.1.1:5000,192.168.1.2:5000,192.168.1.3:5000"

	# also add other commands to check health of cluster...

	arakoonInstance.start()
	# will block so next lines not executed

	arakoonInstance.stop()
	arakoonInstance.isrunning()


	# when starting from empty situation
	q.manage.servers.arakoon.get("anInstanceName")
	arakoonInstance.stop()


	j.application.stop()


	#@todo (P3) implement better arakoon mgmt class
