from JumpScale import j
import os

from JumpScale.core.config.IConfigBase import ConfigManagementItem, GroupConfigManagement, SingleConfigManagement
from JumpScale.core.config.JConfigBase import ConfiguredItem, ConfiguredItemGroup
from JumpScale.core.config.ConfigLib import ItemGroupClass, ItemSingleClass

class BitbucketConfigManagementItem(ConfigManagementItem):
    CONFIGTYPE = "bitbucket"
    DESCRIPTION = "bitbucket account, key = accountname"
    KEYS = {"login": "","passwd":"Password"}

    def ask(self):
        self.dialogAskString('login', 'Enter login')
        self.dialogAskPassword('passwd', 'Enter password for user "%s"' % self.params["login"])

    def save(self):
        super(BitbucketConfigManagementItem, self).save()
        hgpath = '{0}/.hgrc'.format(os.path.expanduser('~'))
        hgini = j.tools.inifile.open(hgpath)
        if self.params:
            hgini.addSection('auth')
        prefix = 'bb_%s.%%s' % self.itemname
        hgini.addParam('auth', prefix % 'prefix', 'bitbucket.org/%s' % self.itemname)
        hgini.addParam('auth', prefix % 'schemes', 'http https')
        hgini.addParam('auth', prefix % 'username', self.params.get('login', ''))
        hgini.addParam('auth', prefix % 'password', self.params.get('passwd', ''))


BitbucketConfigManagement = ItemGroupClass(BitbucketConfigManagementItem)
