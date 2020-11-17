import os
import json
import time
import codecs
import plistlib
import tempfile
import subprocess
from pathlib import Path
from packaging import version
import lyrebird
from lyrebird.log import get_logger
from . import wda_helper

_log = get_logger()

ideviceinstaller = None
idevice_id = None
idevicescreenshot = None
ideviceinfo = None

root = os.path.dirname(__file__)
model_json = os.path.abspath(os.path.join(root, 'config/comparison_table_model.json'))
storage = lyrebird.get_plugin_storage()
screenshot_dir = os.path.abspath(os.path.join(storage, 'screenshot'))

PLIST_PATH = os.path.join(storage, 'plist')
SYSTEM_BIN = Path('/usr/local/bin')

ios_driver = wda_helper.Helper()

def check_environment():
    """
    检查用户环境，第三方依赖是否正确安装。
    :return:
    """
    global ideviceinstaller, idevice_id, idevicescreenshot, ideviceinfo

    # Check libmobiledevice, action when unavailable : block
    p = subprocess.run('brew info --json libimobiledevice', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    code, output, err_str = p.returncode, p.stdout.decode(), p.stderr.decode()
    if err_str or code or not output:
        raise LibmobiledeviceError(f'Get libmobiledevice info error: {err_str}')

    try:
        libimobiledevice_info = json.loads(output)
    except Exception:
        raise LibmobiledeviceError(f'Get unknown libmobiledevice info: {output}')

    if not isinstance(libimobiledevice_info, list) and not len(libimobiledevice_info):
        raise LibmobiledeviceError(f'Get unknown libmobiledevice info: {output}')

    # Check idevice_id, action when unavailable : block
    idevice_id_keywords = 'idevice_id'
    idevice_id = SYSTEM_BIN/idevice_id_keywords
    err_msg = check_environment_item(idevice_id_keywords, idevice_id)
    if err_msg:
        idevice_id = None
        raise IdeviceidError(err_msg)

    # Check ideviceinfo, action when unavailable : block
    ideviceinfo_keywords = 'ideviceinfo'
    ideviceinfo = SYSTEM_BIN/ideviceinfo_keywords
    err_msg = check_environment_item(ideviceinfo_keywords, ideviceinfo)
    if err_msg:
        ideviceinfo = None
        raise IdeviceinfoError(err_msg)

    env_err_msg = []

    # Check ideviceinstaller, action when unavailable : warning
    lib_version = libimobiledevice_info[0].get('versions', {}).get('stable')
    lib_version = '1.2.0' if version.parse(lib_version) < version.parse('1.3.0') else '1.3.0'

    ideviceinstaller_keywords = 'ideviceinstaller'
    ideviceinstaller = Path(__file__).parent/'bin'/lib_version/ideviceinstaller_keywords
    err_msg = check_environment_item(ideviceinstaller_keywords, ideviceinstaller)
    if err_msg:
        env_err_msg.append(err_msg)
        ideviceinstaller = None

    # Check idevicescreenshot, action when unavailable : warning
    idevicescreenshot_keywords = 'idevicescreenshot'
    idevicescreenshot = SYSTEM_BIN/idevicescreenshot_keywords
    temp_file = tempfile.NamedTemporaryFile().name
    err_msg = check_environment_item(idevicescreenshot_keywords, idevicescreenshot, sub_command=temp_file)
    if err_msg:
        env_err_msg.append(err_msg)
        idevicescreenshot = None

    if env_err_msg:
        _log.error('iOS Plugin environment warning:\n' + '.\n'.join(env_err_msg))

def check_environment_item(command, path, sub_command=''):
    if not Path(path).exists():
        return f'Command `{command}` not found, check your libimobiledevice'

    p = subprocess.run(f'{str(path)} {sub_command}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err_str = p.stderr.decode()
    return f'Execute command `{command}` error: {err_str}' if err_str else ''

def read_plist(plist_path):
    return plistlib.readPlist(plist_path)


class Apps:
    """
    应用基类，属性为 plist, bundle_id，提供两个方法，获取app的列表，和获取指定app的详细信息
    """

    def __init__(self):
        self._plist = None
        self.bundle_id = None
        self.app_info = {}

    @property
    def plist(self):
        return self._plist

    @plist.setter
    def plist(self, name):
        plist_path = os.path.join(PLIST_PATH, name)
        if os.path.exists(plist_path):
            self._plist = plist_path

    @property
    def apps(self):
        return read_plist(self.plist)

    @property
    def app_key(self):
        return {
            "CFBundleName": "AppName",
            "CFBundleIdentifier": "BundleID",
            "CFBundleShortVersionString": "VersionNumber",
            "CFBundleVersion": "BuildNumber"
        }

    def app(self, bundle_id):
        for app in self.apps:
            if bundle_id in app.get('CFBundleIdentifier'):
                return app
        _log.debug(f'{bundle_id} is not found in this device!')
        return {}

    def get_app_list(self):
        app_list = []
        for app in self.apps:
            tmp = {}
            tmp["app_name"] = app.get('CFBundleName')
            tmp['bundle_id'] = app.get('CFBundleIdentifier')
            app_list.append(tmp)
        return app_list

    def get_app_info(self, bundle_id):
        for k, v in self.app_key.items():
            self.app_info[v] = self.app(bundle_id).get(k)
        return self.app_info


class Device:
    """
    设备基类，主要属性包含 device_id, model, os_version等，主要方法包括截屏，获取信息等
    """

    def __init__(self, device_id):
        self.device_id = device_id
        self.model = None
        self.is_jailbreak = None
        self.phone_number = None
        self.os_version = None
        self.device_name = None
        self.sn = None
        self._log_process = None
        self._log_cache = []
        self._log_crash_cache = []
        self._log_file = None
        self._screen_shot_file = None
        self._anr_file = None
        self._crash_file_list = []
        self._device_info = None
        self._apps_list = None
        self.start_catch_log = False
        self._pid = None

    @property
    def log_file(self):
        return self._log_file

    @property
    def screen_shot_file(self):
        return self._screen_shot_file

    @property
    def anr_file(self):
        return self._anr_file

    @property
    def crash_file_list(self):
        return self._crash_file_list

    @classmethod
    def read_line(cls, line):
        res = subprocess.run(f'{ideviceinfo} -u {line}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        lines = res.stdout.decode()

        device_info = [info for info in lines.split('\n') if info]
        _device = cls(line)
        if len(device_info) < 2:
            _log.error(f'Read device info line error. {lines}')
        for info in device_info:
            info_kv = info.split(':')
            if info_kv[0] == 'ProductType':
                _device.model = cls(line).convert_model(model=info_kv[1].strip())
            if info_kv[0] == 'BrickState':
                _device.is_jailbreak = info_kv[1].strip()
            if info_kv[0] == 'PhoneNumber':
                _device.phone_number = info_kv[1].strip()
            if info_kv[0] == 'ProductVersion':
                _device.os_version = info_kv[1].strip()
            if info_kv[0] == 'DeviceName':
                _device.device_name = info_kv[1].strip()
            if info_kv[0] == 'SerialNumber':
                _device.sn = info_kv[1].strip()
        return _device

    def convert_model(self, model):
        model_dict = json.loads(codecs.open(model_json, 'r', 'utf-8').read())
        return model_dict.get(model)

    @property
    def device_info(self):
        if not self._device_info:
            self._device_info = self.get_properties()
        return self._device_info

    def start_app(self, bundle_id, ip, port):
        ios_driver.bundle_id = bundle_id
        ios_driver.environment = {
            'mock': f'http://{ip}:{port}/mock',
            'closeComet': True,
            'urlscheme': True
        }
        try:
            ios_driver.start_app()
        except Exception as e:
            return str(e)
        return ''

    def stop_app(self):
        try:
            ios_driver.stop_app()
        except AttributeError as e:
            return str(e)
        return ''

    def get_properties(self):
        p = subprocess.run(f'{ideviceinfo} -u {self.device_id}', shell=True, stdout=subprocess.PIPE)
        if p.returncode == 0:
            return p.stdout.decode().split('\n')

    def get_app_info(self, bundle_id):
        self.get_device_plist(self.device_id)
        apps = Apps()
        apps.plist = self.device_id + '.plist'
        return apps.get_app_info(bundle_id)

    def get_device_plist(self, device_id):
        plist_path = '%s/%s.plist' % (PLIST_PATH, self.device_id)
        if not os.path.exists(PLIST_PATH):
            os.mkdir(PLIST_PATH)
        if not ideviceinstaller:
            raise IdeviceinstallerError('Command `ideviceinstaller` is not ready! Check your libimobiledevice')
        _cmd = f'{ideviceinstaller} -u {self.device_id} -l -o xml'

        with open(plist_path, 'w') as output:
            p = subprocess.Popen(_cmd, stdout=output, shell=True)
            p.wait()

    def get_apps_list(self, device_id):
        self.get_device_plist(device_id)
        apps = Apps()
        apps.plist = self.device_id + '.plist'
        return apps.get_app_list()

    def stop_log(self):
        if self._log_process:
            self._log_process.kill()
            self._log_process = None

    def take_screen_shot(self):
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
        file_name = self.model.replace(' ', '_')
        timestamp = int(time.time())
        screen_shot_file = os.path.abspath(os.path.join(screenshot_dir, f'{file_name}_{timestamp}.png'))
        p = subprocess.run(f'{idevicescreenshot} -u {self.device_id} {screen_shot_file}',
                           shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = {
            'returncode': p.returncode,
            'result': p,
            'screen_shot_file': screen_shot_file,
            'timestamp': timestamp
        }
        return result

    def to_dict(self):
        device_info = {k: self.__dict__[k] for k in self.__dict__ if not k.startswith('_')}
        # get additional device info
        prop_lines = self.device_info
        if not prop_lines:
            return device_info
        return device_info


def devices():
    """

    :type    dict
    :return: online_devices object of online devices
    """
    res = subprocess.run(f'{idevice_id} -l', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = res.stdout.decode()
    err_str = res.stderr.decode()

    # Get devices error
    if len(output) <= 0 < len(err_str):
        print('Get devices list error', err_str)
        return []
    lines = [line for line in output.split('\n') if line]
    online_devices = {}
    if len(lines) == 0:
        return online_devices
    for line in lines:
        device = Device.read_line(line)
        online_devices[device.device_id] = device

    return online_devices


class LibmobiledeviceError(Exception):
    pass


class IdeviceinstallerError(Exception):
    pass


class IdeviceidError(Exception):
    pass


class IdeviceinfoError(Exception):
    pass
