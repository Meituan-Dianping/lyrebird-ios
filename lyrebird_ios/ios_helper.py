import os, plistlib, subprocess, threading, codecs, json, time
from pathlib import Path
import lyrebird
from lyrebird import context
from lyrebird.log import get_logger
from .helper import config

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

PLUGIN_ROOT_PATH = Path('~', '.lyrebird/plugins/lyrebird_ios').expanduser()
PLIST_PATH = os.path.join(PLUGIN_ROOT_PATH, 'plist')
error_msg = None

if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)


if not os.path.exists(crash_dir):
    os.makedirs(crash_dir)


class libimobiledeviceError(Exception):
    pass


class ideviceinstallerError(Exception):
    pass


def check_environment():
    """
    检查用户环境，第三方依赖是否正确安装。
    :return:
    """
    global ideviceinstaller, idevice_id, idevicescreenshot, ideviceinfo, idevicesyslog, error_msg

    if not os.path.exists('/usr/local/bin/ideviceinfo'):
        error_msg = {"show_error": True,
                     "user_message": "No ideviceinfo program found, need libimobiledevice dependencies with Homebrew, See README Help Center"}
        time.sleep(20)
        raise libimobiledeviceError('No libimobiledevice program found, See README Help Center')
    else:
        p = subprocess.Popen('/usr/local/bin/ideviceinfo', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        err = p.stderr.read().decode()
        if len(err):
            error_msg = {"show_error": True,
                         "user_message": "ideviceinfo program found but not working with error -> %s, See README Help Center" % err}
            time.sleep(20)
            raise libimobiledeviceError('ideviceinfo program found but not working with error -> %s, See README Help Center' % err)

    if not os.path.exists('/usr/local/bin/ideviceinstaller'):
        error_msg = {"show_error": True,
                     "user_message": "No ideviceinstaller program found, need ideviceinstaller dependencies use Homebrew, See README Help Center"}
        time.sleep(20)
        raise ideviceinstallerError("No ideviceinstaller program found, need ideviceinstaller dependencies use Homebrew, See README Help Center")

    if not os.path.exists('/usr/local/bin/idevicescreenshot'):
        error_msg = {"show_error": True,
                     "user_message": "No idevicescreenshot program found, need libimobiledevice dependencies use Homebrew, See README Help Center"}
        time.sleep(20)
        raise libimobiledeviceError('No idevicescreenshot program found, See README Help Center')

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
        conf = config.load()
        if hasattr(conf, 'app_info'):
            return config.load().app_info
        else:
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
        self._screen_shot_file = os.path.abspath(os.path.join(tmp_dir, 'android_screenshot_%s.png' % self.device_id))
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
            raise libimobiledeviceError('Failed to got device info, Please make sure \'deviceinfo\' command is working on your system.')
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

                # self.crash_checker(line)
                # self.anr_checker(line)
                self._log_cache.append(line.decode(encoding='UTF-8', errors='ignore'))

                if len(self._log_cache) >= 5000:
                    context.application.socket_io.emit('log', self._log_cache, namespace='/iOS-plugin')
                    log_file.writelines(self._log_cache)
                    log_file.flush()
                    self._log_cache = []
        threading.Thread(target=log_handler, args=(p,)).start()

    def crash_checker(self, line):
        crash_log_path = os.path.join(crash_dir, 'android_crash_%s.log' % self.device_id)

        if str(line).find('FATAL EXCEPTION') > 0:
            self.start_catch_log = True
            self._log_crash_cache.append(str(line))
            lyrebird.publish('crash', 'android', path=crash_log_path, id=self.device_id)
        elif str(line).find('AndroidRuntime') > 0 and self.start_catch_log:
            self._log_crash_cache.append(str(line))
        else:
            self.start_catch_log = False
            with codecs.open(crash_log_path, 'w') as f:
                f.write('\n'.join(self._log_crash_cache))

    def anr_checker(self, line):
        if str(line).find('ANR') > 0 and str(line).find('ActivityManager') > 0:
            self.get_anr_log()

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
        p = subprocess.run(f'{idevicescreenshot} -u {self.device_id} {tmp_dir}/{file_name}.png', shell=True)
        if p.returncode == 0:
            return os.path.abspath(os.path.join(tmp_dir, '%s.png' % file_name))
        else:
            return False

    def to_dict(self):
        device_info = {k: self.__dict__[k] for k in self.__dict__ if not k.startswith('_')}
        # get additional device info
        prop_lines = self.device_info
        if not prop_lines:
            return device_info

        for line in prop_lines:
            # 基带版本
            if 'ro.build.expect.baseband' in line:
                baseband = line[line.rfind('[')+1:line.rfind(']')].strip()
                device_info['baseBand'] = baseband
            # 版本号
            if 'ro.build.id' in line:
                build_id = line[line.rfind('[') + 1:line.rfind(']')].strip()
                device_info['buildId'] = build_id
            # Android 版本
            if 'ro.build.version.release' in line:
                build_version = line[line.rfind('[') + 1:line.rfind(']')].strip()
                device_info['releaseVersion'] = build_version
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
