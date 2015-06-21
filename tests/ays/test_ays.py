import unittest
import subprocess
import os
import socket
import time


class AysTest(unittest.TestCase):
    """
    Test Case to test @ys different scenarios
    and make sure everything works OK.
    """

    def setUp(self):
        pass
    
    def tearDown(self):
        """
        clean all installed test packages (usually by deleting files  /opt/jumpscale7/hrd/apps/jumpscale__test*
        clean all temp files created for test purposes
        """
        subprocess.Popen('rm -rf /opt/jumpscale7/hrd/apps/jumpscale__test*', shell=True, stdout=subprocess.PIPE)
        p = subprocess.Popen('rm /tmp/test', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_simple_install_with_dependencies(self):
        """
        Install (test) package
            - Check it's installed
            - Checek dependencies installed
                * test2
                * test3
                * test4
        """
        p = subprocess.Popen('ays install -n test', shell=True,  stdout=subprocess.PIPE)
        # Just read the output -- don't print it as it it's not needed
        p.stdout.readlines()
            
        self.assertTrue(os.path.exists('/opt/jumpscale7/hrd/apps/jumpscale__test__main/actions.py'), 'test installation failure')
        self.assertTrue(os.path.exists('/opt/jumpscale7/hrd/apps/jumpscale__test__main/service.hrd'), 'test installation failure')
        self.assertTrue(os.path.exists('/opt/jumpscale7/hrd/apps/jumpscale__test2__main/actions.py'), 'test2 installation failure')
        self.assertTrue(os.path.exists('/opt/jumpscale7/hrd/apps/jumpscale__test2__main/service.hrd'), 'test2 installation failure')
        self.assertTrue(os.path.exists('/opt/jumpscale7/hrd/apps/jumpscale__test3__main/actions.py'), 'test3 installation failure')
        self.assertTrue(os.path.exists('/opt/jumpscale7/hrd/apps/jumpscale__test3__main/service.hrd'), 'test3 installation failure')
        self.assertTrue(os.path.exists('/opt/jumpscale7/hrd/apps/jumpscale__test4__main/actions.py'), 'test4 installation failure')
        self.assertTrue(os.path.exists('/opt/jumpscale7/hrd/apps/jumpscale__test4__main/service.hrd'), 'test4 installation failure')
        self.assertFalse(os.path.exists('/opt/jumpscale7/hrd/apps/jumpscale__test5__main/actions.py'), 'test4 installation failure')
        self.assertFalse(os.path.exists('/opt/jumpscale7/hrd/apps/jumpscale__test5__main/service.hrd'), 'test4 installation failure')
        
    def test_start_package(self):
        """
        Package test5 on start should create the file /tmp/test
        with the contents "test"
        """
        p = subprocess.Popen('ays install -n test5', shell=True,  stdout=subprocess.PIPE)
        p.communicate()
        p2 = subprocess.Popen('ays start -n test5', shell=True,  stdout=subprocess.PIPE)
        p2.communicate()
        
        self.assertTrue(os.path.exists('/tmp/test'), 'test5 package failed to start')
        self.assertEquals(open('/tmp/test').read(), 'test\n')
    
    
    def test_instance_hrd_params(self):
        """
        test6 package instance.hrf contains param.test=test type:str
        this should be available after installation
        """
        p = subprocess.Popen('ays install -n test6', shell=True,  stdout=subprocess.PIPE)
        p.communicate()
        entry = open('/opt/jumpscale7/hrd/apps/jumpscale__test6__main/service.hrd').readlines()[0]
        entry = entry.replace(' ', '')
        self.assertEquals(entry, "instance.param.test='test'\n")

    def test_stop_package(self):
        """
        test7 package on stop hould create the file /tmp/test_stop
        with the contents "stop"
        """
        p = subprocess.Popen('ays install -n test7', shell=True,  stdout=subprocess.PIPE)
        p.communicate()
        p2 = subprocess.Popen('ays stop -n test7', shell=True,  stdout=subprocess.PIPE)
        p2.communicate()
        self.assertTrue(os.path.exists('/tmp/test_stop'), 'test7 package failed to stop')
        self.assertEquals(open('/tmp/test_stop').read(), 'stop\n')
        
    def test_install_simple_webserver(self):
        """
        Install simpletestwebserver
        Make sure it is properly installed
        and that binaries are doenloaded properly.
        """
        p = subprocess.Popen('ays install -n test_simple_webserver', shell=True,  stdout=subprocess.PIPE)
        p.communicate()
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1',9345))
        
        #Test port open
        self.assertEquals(result, 0, 'Simplewebserver did not start correctrly')
        #test files are installed correctly
        self.assertTrue(os.path.exists('/opt/jumpscale7/hrd/apps/jumpscale__test_simple_webserver__main/service.hrd'), 'Simplewebserver was not installed correctly')
        self.assertTrue(os.path.exists('/opt/jumpscale7/hrd/apps/jumpscale__test_simple_webserver__main/actions.py'), 'Simplewebserver was not installed correctly')
        # test binaries are cloned
        self.assertTrue(os.path.exists('/opt/jumpscale7/apps/simpletestwebserver/simplewebserver.py'), 'Simplewebserver was not installed correctly')
        self.assertTrue(os.path.exists('/opt/jumpscale7/apps/simpletestwebserver/README.md'), 'Simplewebserver was not installed correctly')
        
        # Stopping package
        p = subprocess.Popen('ays stop -n test_simple_webserver', shell=True,  stdout=subprocess.PIPE)
        p.communicate()
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1',9345))
        #Test port closed
        self.assertNotEquals(result, 0, 'Simplewebserver did not stop correctrly')
        
if __name__ == '__main__':
    unittest.main()