from flask import request, jsonify, send_from_directory
from lyrebird import context
import lyrebird
from .device_service import DeviceService
from .helper import config
import codecs
import time
import os
import socket
import json
from lyrebird.log import get_logger
from pathlib import Path
import traceback
from .device_service import DeviceService

_log = get_logger()

device_service = DeviceService()
storage = lyrebird.get_plugin_storage()
tmp_dir = os.path.abspath(os.path.join(storage, 'tmp'))
anr_dir = os.path.abspath(os.path.join(storage, 'anr'))

if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)


class MyUI(lyrebird.PluginView):
    """
    插件视图子类
    提供后端处理逻辑，API，管理插件主页面等
    """
    def index(self):
        """
        插件首页        
        """
        return codecs.open(self.get_package_file_path('templates/index.html'), 'r', 'utf-8').read()

    @staticmethod
    def info():
        """
        获取设备信息
        :return:
        """
        device_info = {'device': None, 'app': None}
        if len(device_service.devices) == 0:
            return jsonify(device_info)
        device = list(device_service.devices.values())[0]
        device_prop = device.to_dict()
        device_info['device'] = {'UDID': device_prop['device_id'], 'Model': device_prop['model'], 'Version': device_prop['os_version']}

        conf = config.load()
        if hasattr(conf, 'default_app'):
            default_app = conf.default_app
        else:
            default_app = ''

        device_info['app'] = device.get_app_info(default_app)
        return jsonify(device_info)

    def device_list(self):
        return jsonify(device_service.devices_to_dict())

    def device_detail(self, device_id):
        return "\n".join(device_service.devices.get(device_id).device_info)

    def last_package_name(self):
        conf = config.load()
        return jsonify({"packageName": conf.package_name})

    def app_info(self, device_id, bundle_id):

        # conf = config.load()
        # conf.package_name = package_name
        # conf.save()
        device = device_service.devices.get(device_id)
        return jsonify(device.get_app_info(bundle_id))

    def app_list(self, device_id):
        device = device_service.devices.get(device_id)
        if device:
            app_list = device.get_apps_list(device_id)
            return jsonify(app_list)
        else:
            return context.make_fail_response('No device_id found. Are you sure?')

    def logcat_start(self, device_id):
        print('Logcat start', device_id)
        device_service.start_log_recorder(device_id)

    def take_screen_shot(self, device_id):
        device = device_service.devices.get(device_id)
        img_path = device.take_screen_shot()
        if img_path:
            return jsonify({'imgUrl': '/ui/plugin/iOS/api/src/screenshot/%s?time=%s' % (device_id, time.time())})
        else:
            return context.make_fail_response('Could not start screenshot service! '
                                              'Please make sure the idevicescreenshot command works correctly')

    def get_screenshot_image(self, device_id):
        return send_from_directory(tmp_dir, '%s.png' % device_service.devices.get(device_id).model.replace(' ', '_'))

    def make_dump_data(self, path):
        device_data = {}
        device_data['name'] = os.path.basename(path)
        device_data['path'] = path
        return device_data

    def dump_data(self):
        """
        获取所有设备相关信息，包括设备日志，崩溃日志，ANR日志，快照图片，APP_INFO等
        :return: name, path
        e.g
        [
            {
                "name": "ios_log_{imei}.log",
                "path": "/Users/lee/.lyrebird/plugins/lyrebird_ios/tmp/android_log_{imei}.log"
            },
            {
                "name": "ios_screenshot_{imei}.png",
                "path": "/Users/lee/.lyrebird/plugins/lyrebird_ios/tmp/android_screenshot_{imei}.png"
            }
        ]
        """
        res = []
        devices = device_service.devices

        for udid in devices:
            device = devices[udid]
            if device.log_file:
                res.append(self.make_dump_data(device.log_file))
            if device.take_screen_shot():
                res.append(self.make_dump_data(device.take_screen_shot()))

        return jsonify(res)

    def start_app(self, device_id, package_name):
        """

        :param device_id:
        :return:
        """
        device = device_service.devices.get(device_id)
        if not device:
            device = list(device_service.devices.values())[0]
        conf = config.load()
        app = device.package_info(conf.package_name)
        device.stop_app(conf.package_name)
        port = lyrebird.context.application.conf.get('mock').get('port')
        device.start_app(app.launch_activity, get_ip(), port)
        return context.make_ok_response()

    def stop_app(self, device_id, package_name):
        """

        :param device_id:
        :return:
        """
        device = device_service.devices.get(device_id)
        if not device:
            device = list(device_service.devices.values())[0]
        conf = config.load()
        device.stop_app(conf.package_name)
        return context.make_ok_response()

    def dump(self, device_id):
        """
        保存截图 设备信息 日志 app信息
        :param device_id:
        :return: 所有信息文件绝对路径 json list
        """
        device = device_service.devices.get(device_id)
        if device:
            device.take_screen_shot()

        return jsonify([device.log_file, device.screen_shot_file, self.get_app_info_file_path(device), self.get_prop_file_path(device, device_id)])

    def get_prop_file_path(self, device, device_id):
        device_prop_file_path = os.path.abspath(os.path.join(tmp_dir, '%s.info.txt' % device_id))
        device_prop = device.device_info
        device_prop_file = codecs.open(device_prop_file_path, 'w', 'utf-8')
        for prop_line in device_prop:
            device_prop_file.write(prop_line+'\n')
        device_prop_file.close()

        return device_prop_file_path

    def get_app_info_file_path(self, device):
        conf = config.load()
        app_info_file_path = ''
        if conf.package_name:
            app_info_file_path = os.path.abspath(os.path.join(tmp_dir, '%s.info.txt' % conf.package_name))
            app_info = device.package_info(conf.package_name)
            app_info_file = codecs.open(app_info_file_path, 'w', 'utf-8')
            app_info_file.writelines(app_info.raw)
            app_info_file.close()

        return app_info_file_path

    def get_default_conf(self):
        conf = config.load()
        return jsonify(conf.__dict__)

    def check_env(self):
        from .ios_helper import error_msg
        return jsonify(error_msg)

    def desc(self):
        device_info = self.info().json
        if device_info.get('device'):
            return jsonify({
                "code": 0,
                "data": "\n\n【设备应用信息】\n" +
                        "设备类型： %s\n" % device_info.get('device').get('Model') +
                        "设备系统： %s\n\n" % device_info.get('device').get('Version') +
                        "应用名称： %s\n" % device_info.get('app').get('AppName') +
                        "Version：  %s\n" % device_info.get('app').get('VersionNumber') +
                        "Build： %s\n" % device_info.get('app').get('BuildNumber') +
                        "BundleID： %s" % device_info.get('app').get('BundleID')
            })
        else:
            return context.make_fail_response('No device found, is it plugged in?')


    def on_create(self):
        """
        插件初始化函数（必选）
        """
        # 设置模板目录（可选，设置模板文件目录。默认值templates）

        # for overbridge
        self.add_url_rule('/api/info', view_func=self.info)
        # for Bugit
        self.add_url_rule('/api/desc', view_func=self.desc)
        self.add_url_rule('/api/conf', view_func=self.get_default_conf)
        # Dump所有信息
        # self.add_url_rule('/api/dump/<string:device_id>', view_func=self.dump)
        # 获取设备列表
        self.add_url_rule('/api/devices', view_func=self.device_list)
        # 设备详情
        self.add_url_rule('/api/device/<string:device_id>', view_func=self.device_detail)
        # self.add_url_rule('/api/package_name', view_func=self.last_package_name)
        # 获取app详情
        self.add_url_rule('/api/apps/<string:device_id>/<string:bundle_id>', view_func=self.app_info)
        # 进行截图
        self.add_url_rule('/api/screenshot/<string:device_id>', view_func=self.take_screen_shot)
        # 获取截图
        self.add_url_rule('/api/src/screenshot/<string:device_id>', view_func=self.get_screenshot_image)
        # 启动应用
        # self.add_url_rule('/api/start_app/<string:device_id>/<string:package_name>', view_func=self.start_app)
        # self.add_url_rule('/api/stop_app/<string:device_id>/<string:package_name>', view_func=self.stop_app)
        # 获取设备应用列表
        self.add_url_rule('/api/apps/<string:device_id>', view_func=self.app_list)
        # 获取资源信息
        self.add_url_rule('/api/dump', view_func=self.dump_data)
        # 检查环境
        self.add_url_rule('/api/check-env', view_func=self.check_env)
        # 启动设备监听服务
        lyrebird.start_background_task(device_service.run)

    @staticmethod
    def get_icon():
        # 设置插件 icon
        return 'fa fa-fw fa-apple'

    @staticmethod
    def get_title():
        # 设置插件的名称
        return 'iOS'

    def default_conf(self):
        current_dir = Path(__file__).parent
        conf_path = Path(current_dir, './config/conf.json')
        with codecs.open(conf_path, 'r', 'utf-8') as f:
            return json.loads(f.read())


def get_ip():
    """
    获取当前设备在网络中的ip地址

    :return: IP地址字符串
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('google.com', 80))
    return s.getsockname()[0]
