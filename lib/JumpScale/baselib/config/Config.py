import yaml
from JumpScale import j


class Config(object):
    def get(self, app, instance):
        """
        Gets a configured instance
        :param app: (str) name of the app
        :param instance (str) instance of that app
        :return: (dict) instance data
        """
        with open("{}/{}/{}.yml".format(j.dirs.cfgDir, app, instance)) as cfg:
            return yaml.load(cfg)

    def set(self, app, instance, data):
        """
        Configure an instance
        :param app: (str) name of the app
        :param instance (str) instance of that app
        :param data: (dict) data to set for that instance
        """
        if not isinstance(data, dict):
            raise TypeError("data needs to be a dict")
        dir_path = "{}/{}".format(j.dirs.cfgDir, app)
        j.system.fs.createDir(dir_path)
        with open("{}/{}.yml".format(dir_path, instance), "w") as cfg:
            yaml.safe_dump(data, cfg, default_flow_style=False)
    
    def list(self, app):
        """
        Lists all instances for an app
        :param app: (str) name of the app
        :param instance (str) instance of that app
        :return: (list) available instances of that app
        """
        instances = j.system.fs.listFilesInDir("{}/{}".format(j.dirs.cfgDir, app))
        return [j.system.fs.getBaseName(instance).split(".yml")[0] for instance in instances]

    def delete(self, app, instance):
        """
        Deletes a configured instance
        :param app: (str) name of the app
        :param instance (str) instance of that app
        """
        j.system.fs.remove("{}/{}/{}.yml".format(j.dirs.cfgDir, app, instance))