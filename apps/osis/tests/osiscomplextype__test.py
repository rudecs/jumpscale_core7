import unittest
from JumpScale import j
import time

descr = """
basic functioning of osis (test set) for complex types
"""

organization = "jumpscale"
author = "incubaid"
license = "bsd"
version = "1.0"
category = "osis.complextype.testset"
enable=True
priority=3

import JumpScale.grid.osis


class TEST(unittest.TestCase):

    def setUp(self):
        self.client = j.clients.osis.getByInstance('main')
        self.osisclient =j.clients.osis.getCategory(self.client, 'test_complextype', 'project')
   
    def test_set(self):
        # We first set some elements and verify the reponse
        obj = self.osisclient.new()
        obj.descr="test descr"
        for i in range (5):
            task=obj.new_task()
            task.name="a task %s"%i
            task.priority=i
        
        self.assertEqual(obj.getContentKey(), '4e2e3a33a5887669070a2dcc6fc4888a')
        
        ckeyOriginal=obj.getContentKey()

        key,new,changed=self.osisclient.set(obj)
        key2,new,changed=self.osisclient.set(obj)

        print("2x save should have same key")
        self.assertEqual(key, key2)

        print("check 2nd save new & changed are not new or changed")
        self.assertFalse(new)
        self.assertFalse(changed)

        print("test content key does not get modified when set")
        self.assertEqual(ckeyOriginal, obj.getContentKey())

        print("retrieve obj from db")
        obj2=self.osisclient.get(key)
        print("test content key needs to remain same after fetching object")

        self.assertEqual(ckeyOriginal, obj2.getContentKey())

        obj.description="a descr"
        print("obj needs to be different")
        self.assertNotEqual(ckeyOriginal, obj.getContentKey())
        key3,new,changed=self.osisclient.set(obj)
        print("check 3nd save new & changed are False,True for modified obj")
        self.assertFalse(new)
        self.assertTrue(changed)
        print("key should be same")
        self.assertEqual(key, key3)

        obj3=self.osisclient.get(key3)
        print("guid should be same even after content change")
        self.assertEqual(obj3.guid, key)

    def test_find(self):
        # We first set some elements and verify the reponse
        for x in range(2):  #this should not make new elements
            for t in range(5):
                obj = self.osisclient.new()
                obj.name="name%s"%t
                obj.descr="test descr"
                for i in range (5):
                    task=obj.new_task()
                    task.name="a task %s %s"%(t,i)
                    task.priority=i
                key,new,changed=self.osisclient.set(obj)

        start = time.time()
        while start + 5 > time.time():
            items=self.osisclient.simpleSearch({'name': 'name1'})
            if items:
                break
    
        self.assertEqual(len(items), 1) #there should be only 1 (even the fact we stored in 2x, this because of overrule on setguid method)

        while start + 5 > time.time():
            items=self.osisclient.simpleSearch(params={"name":"name3"})
            if items:
                break

        self.assertEqual(len(items), 1) #there should be only 1 (even the fact we stored in 2x, this because of overrule on setguid method)
