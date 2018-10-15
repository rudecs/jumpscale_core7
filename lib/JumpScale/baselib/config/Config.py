import yaml
import os

CFGDIR = "/opt/jumpscale7/cfg"

class Config(object):
    def get(self, app, instance):
        """
        Gets a configured instance
        :param app: (str) name of the app
        :param instance (str) instance of that app
        :return: (dict) instance data
        """
        with open("{}/{}/{}.yml".format(CFGDIR, app, instance)) as cfg:
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
        dir_path = "{}/{}".format(CFGDIR, app)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, 0o755)
        with open("{}/{}.yml".format(dir_path, instance), "w") as cfg:
            yaml.safe_dump(data, cfg, default_flow_style=False)
    
    def list(self, app):
        """
        Lists all instances for an app
        :param app: (str) name of the app
        :param instance (str) instance of that app
        :return: (list) available instances of that app
        """
        dir_path = "{}/{}".format(CFGDIR, app)
        if not os.path.exists(dir_path):
            return []
        instances = os.listdir(dir_path)
        return [instance.split(".yml")[0] for instance in instances]

    def delete(self, app, instance):
        """
        Deletes a configured instance
        :param app: (str) name of the app
        :param instance (str) instance of that app
        """
        os.remove("{}/{}/{}.yml".format(CFGDIR, app, instance))