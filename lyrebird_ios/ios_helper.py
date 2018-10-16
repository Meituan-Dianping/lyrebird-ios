import os, plistlib, subprocess, threading, codecs, json, time
import lyrebird
from lyrebird import context
from lyrebird.log import get_logger

_log = get_logger()

ideviceinstaller = None
idevice_id = None
idevicescreenshot = None
ideviceinfo = None
idevicesyslog = None

root = os.path.dirname(__file__)
static = os.path.abspath(os.path.join(root, 'static'))
model_json = os.path.abspath(os.path.join(root, 'config/comparison_table_model.json'))
storage = lyrebird.get_plugin_storage()

tmp_dir = os.path.abspath(os.path.join(storage, 'tmp'))
crash_dir = os.path.abspath(os.path.join(storage, 'crash'))

PLIST_PATH = os.path.join(storage, 'plist')
error_msg = None

if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)


if not os.path.exists(crash_dir):
    os.makedirs(crash_dir)


def check_environment():
    """
    检查用户环境，第三方依赖是否正确安装。
    :return:
    """
    global ideviceinstaller, idevice_id, idevicescreenshot, ideviceinfo, idevicesyslog, error_msg

    if not os.path.exists('/usr/local/bin/ideviceinfo'):
        error_msg = {"show_error": True,
                     "user_message": '<b>No ideviceinfo program found, need libimobiledevice '
                                     'dependencies with Homebrew, See <a href="https://github.com/'
                                     'meituan/lyrebird-ios#%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98" '
                                     'target="_blank">README 常见问题</a></b>'}
        time.sleep(20)
        _log.debug('No libimobiledevice program found.')
    else:
        p = subprocess.Popen('/usr/local/bin/ideviceinfo', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        err = p.stderr.read().decode()
        if len(err):
            error_msg = {"show_error": True,
                         "user_message": '<b>ideviceinfo program found but not working with error, '
                                         'See <a href="https://github.com/'
                                         'meituan/lyrebird-ios#%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98" '
                                         'target="_blank">README 常见问题</a></b>'}
            time.sleep(20)
            _log.debug('ideviceinfo program found but not working with error: %s.' % err)

    if not os.path.exists('/usr/local/bin/ideviceinstaller'):
        error_msg = {"show_error": True,
                     "user_message": '<b>No ideviceinstaller program found, '
                                     'dependencies with Homebrew, See <a href="https://github.com/'
                                     'meituan/lyrebird-ios#%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98" '
                                     'target="_blank">README 常见问题</a></b>'}
        time.sleep(20)
        _log.debug("No ideviceinstaller program found.")

    if not os.path.exists('/usr/local/bin/idevicescreenshot'):
        error_msg = {"show_error": True,
                     "user_message": '<b>No idevicescreenshot program found, '
                                     'dependencies with Homebrew, See <a href="https://github.com/'
                                     'meituan/lyrebird-ios#%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98" '
                                     'target="_blank">README 常见问题</a></b>'}
        time.sleep(20)
        _log.debug('No idevicescreenshot program found.')

    idevice_id = '/usr/local/bin/idevice_id'
    ideviceinstaller = '/usr/local/bin/ideviceinstaller'
    ideviceinfo = '/usr/local/bin/ideviceinfo'
    idevicesyslog = '/usr/local/bin/idevicesyslog'
    idevicescreenshot = '/usr/local/bin/idevicescreenshot'

    error_msg = {"show_error": False, "user_message": ""}


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
            tmp['label'] = '%s %s' % (app.get('CFBundleName'), app.get('CFBundleIdentifier'))
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

    def start_log(self):
        self.stop_log()

        log_file_name = 'ios_log_%s.log' % self.device_id
        self._log_file = os.path.abspath(os.path.join(tmp_dir, log_file_name))

        p = subprocess.Popen(f'{idevicesyslog} -u {self.device_id}', shell=True, stdout=subprocess.PIPE)

        def log_handler(logcat_process):
            log_file = codecs.open(self._log_file, 'w', 'utf-8')

            while True:
                line = logcat_process.stdout.readline()

                if not line:
                    context.application.socket_io.emit('log', self._log_cache, namespace='/iOS-plugin')
                    log_file.close()
                    return

                self._log_cache.append(line.decode(encoding='UTF-8', errors='ignore'))

                if len(self._log_cache) >= 5000:
                    context.application.socket_io.emit('log', self._log_cache, namespace='/iOS-plugin')
                    log_file.writelines(self._log_cache)
                    log_file.flush()
                    self._log_cache = []
        threading.Thread(target=log_handler, args=(p,)).start()

    @property
    def device_info(self):
        if not self._device_info:
            self._device_info = self.get_properties()
        return self._device_info

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
        p = subprocess.Popen(f'{ideviceinstaller} -u {self.device_id} -l -o xml > {plist_path}', shell=True)
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
        file_name = self.model.replace(' ', '_')
        p = subprocess.run(f'{idevicescreenshot} -u {self.device_id} {tmp_dir}/{file_name}.png', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        err_str = p.stdout.decode()
        if p.returncode == 0:
            return os.path.abspath(os.path.join(tmp_dir, '%s.png' % file_name))
        else:
            _log.error(f'{err_str}')
            return ''

    def to_dict(self):
        device_info = {k: self.__dict__[k] for k in self.__dict__ if not k.startswith('_')}
        # get additional device info
        prop_lines = self.device_info
        if not prop_lines:
            return device_info
        return device_info


def devices():
    """
    devices 用于返回在线的设备示例集合
    :type    字典
    :return: online_devices 对象 (在线的设备)
    """
    check_environment()

    res = subprocess.run(f'{idevice_id} -l', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = res.stdout.decode()
    err_str = res.stderr.decode()

    # 命令执行异常
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
