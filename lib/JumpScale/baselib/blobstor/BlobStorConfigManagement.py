
from JumpScale.core.config.IConfigBase import ConfigManagementItem, GroupConfigManagement, SingleConfigManagement
from JumpScale.core.config.JConfigBase import ConfiguredItem, ConfiguredItemGroup
from JumpScale.core.config.ConfigLib import ItemGroupClass, ItemSingleClass

class BlobStorConfigManagementItem(ConfigManagementItem):
    CONFIGTYPE = 'blobstor'
    DESCRIPTION = 'blobstor connection, key = name'
    KEYS = {
        'ftp': '',
        'http': '',
        'type': 'local',
        'localpath': '',
        'namespace': 'j.'
    }

    def ask(self):
        self.dialogAskChoice('type', 'select type', ['local', 'ftphttp'], 'local')
        self.dialogAskString('namespace', 'Optional Namespace', 'j.')
        self.dialogAskString('ftp', 'Optional FTP Location (full url location with login/passwd)')
        self.dialogAskString('http', 'Optional HTTP Location (for download only)')
        self.dialogAskString('localpath', 'Optional localpath', '/tmp/jumpscale/blobstor')

BlobStorConfigManagement = ItemGroupClass(BlobStorConfigManagementItem)
