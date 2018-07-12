import lyrebird
import os
import codecs
import json
from pathlib import Path
from . import config


class PluginPath:
    _CURRENT_DIR = Path(__file__).parent
    _STORAGE = Path(lyrebird.get_plugin_storage())
    _PLIST = _STORAGE / 'plist'
    _DEFAULT_CONF = Path(_CURRENT_DIR, './config/conf.json')

    def get_config(self):
        """
        Path of conf.json
        
        :return:  conf.json
        """
        return self._STORAGE / 'conf.json'


    def get_plist(self, device_id):
        """
        Path of plist
        
        :param device_id: 
        :return: device_id.plist
        """
        if not self._PLIST.exists():
            self._PLIST.mkdir()
        return os.path.join(self._PLIST, '%s.plist' % device_id)


    def get_default_conf(self):
        """
        Path of plugin's default conf
        
        :return: conf.json
        """
        with codecs.open(self._DEFAULT_CONF, 'r', 'utf-8') as f:
            return json.loads(f.read())

plugin_path = PluginPath()
