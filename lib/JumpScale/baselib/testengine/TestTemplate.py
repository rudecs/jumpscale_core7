import unittest
from JumpScale import j

descr = """
Templates for testing script
"""

organization = "jumpscale"
author = "incubaid"
license = "bsd"
version = "1.0"
category = "app.category.testset"
enable=True
priority=1
send2osis=False


class TEST(unittest.TestCase):

    def setUp(self):
        """
        executed before each test method.
        """
        pass

    def tearDown(self):
        """
        executed after each test method.
        """
        pass

    def test_example(self):
        """
        test method example
        """
        assert True