import unittest
import os
from JumpScale import j
import shutil

class FSWALKER_test(unittest.TestCase):
    def setUp(self):
        os.mkdir('/tmp/FSWALKER_test')
        os.mkdir('/tmp/FSWALKER_test/dir1')
        os.mkdir('/tmp/FSWALKER_test/dir2')
        os.mkdir('/tmp/FSWALKER_test/differentdir3')
        open('/tmp/FSWALKER_test/f.file', 'w').close()
        open('/tmp/FSWALKER_test/dir1/f1.file', 'w').close()
        open('/tmp/FSWALKER_test/dir1/f.donotinclude', 'w').close()
        with open('/tmp/FSWALKER_test/dir2/f2.file', 'w') as f:
            f.write('this is a test file')
        
        os.mkdir('/tmp/FSWALKER_test_tolink')
        os.mkdir('/tmp/FSWALKER_test_tolink/dir1link')
        os.mkdir('/tmp/FSWALKER_test_tolink/dir2link')
        os.mkdir('/tmp/FSWALKER_test_tolink/differentdir3link')
        open('/tmp/FSWALKER_test_tolink/flink.file', 'w').close()
        open('/tmp/FSWALKER_test_tolink/dir1link/f1link.file', 'w').close()
        os.symlink('/tmp/FSWALKER_test_tolink', '/tmp/FSWALKER_test/linked')

        self.root = '/tmp/FSWALKER_test/'
    
    def tearDown(self):
        shutil.rmtree('/tmp/FSWALKER_test')
        shutil.rmtree('/tmp/FSWALKER_test_tolink')

    def registerType(self, ttype):
        self.assertTrue(True)
    
    def test_find(self):
        fswalker = j.base.fswalker.get()
        result = fswalker.find(self.root, includeFolders=True, includeLinks=True, pathRegexIncludes={}, pathRegexExcludes={'F':['.*.donotinclude']}, followlinks=True, childrenRegexExcludes=['.*/log/.*', '/dev/.*', '/proc/.*'], mdserverclient=None)
        print result
        self.assertRegexpMatches(str(result.values()), '.*f2.*')
        self.assertNotRegexpMatches(str(result.values()), '.*.donotinclude')

if __name__ == '__main__':
    unittest.main()
