import lyrebird
import os
import codecs
import json
from pathlib import Path


class PluginPath:
    _CURRENT_DIR = Path(__file__).parent
    _STORAGE = Path(lyrebird.get_plugin_storage())
    _PLIST = _STORAGE / 'plist'

    def get_plist(self, device_id):
        """
        Path of plist
        
        :param device_id: 
        :return: device_id.plist
        """
        if not self._PLIST.exists():
            self._PLIST.mkdir()
        return os.path.join(self._PLIST, '%s.plist' % device_id)

plugin_path = PluginPath()
