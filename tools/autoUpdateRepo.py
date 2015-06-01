import time
import BaseHTTPServer
import sys
HOST_NAME = '0.0.0.0' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 9000 # Maybe set this to 9000.
PROJECT_PATH = '/opt/code/git/www-ovs/'

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(self):
        """Respond to a GET request."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
                
        if self.path == "/updaterepo":
            self.updateRepo()
            
        
    def updateRepo(self):
        print "Now Updating repo"
        import subprocess
        subprocess.Popen("cd %s && git config remote.origin.url  git@git.aydo.com:ovs/www-ovs.git && git reset --hard && git pull && hugo" % PROJECT_PATH, shell=True)

if __name__ == '__main__':
    PROJECT_PATH = sys.argv[1]
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)