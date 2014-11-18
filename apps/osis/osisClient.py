from JumpScale import j

j.application.start("osisclient")

import JumpScale.grid.osis


if __name__ == '__main__':

    client = j.core.osis.getClientByInstance('main')


    def testClass():
        proj_class=j.core.osis.getOsisModelClass("test_complextype","project")
        project=proj_class()
        project.new_task()

    testClass()

    def testSet10(client):
        for i in range(10):
            obj = client.new()
            obj.name="test%s" % i
            key, new, changed = client.set(obj)

        obj = client.get(key)

        print(obj)

        return obj

    print(client.listNamespaces())

    def test1():
        user=j.core.osis.getClientForCategory(client,"system","user")
        obj=user.new()
        obj.id="jan"
        obj.description="test"
        guid,new,changed=user.set(obj)
        print(user.get(guid))

    test1()

    # from IPython import embed
    # print "DEBUG NOW main in test script osis"
    # embed()



    j.application.stop()
