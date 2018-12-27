from flask import request, jsonify, send_from_directory
from lyrebird import context
import lyrebird
import codecs
import time
import os
import socket
from lyrebird.log import get_logger
from .device_service import DeviceService

_log = get_logger()

device_service = DeviceService()
storage = lyrebird.get_plugin_storage()
tmp_dir = os.path.abspath(os.path.join(storage, 'tmp'))
anr_dir = os.path.abspath(os.path.join(storage, 'anr'))
screenshot_dir = os.path.abspath(os.path.join(storage, 'screenshot'))

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

    def info(self):
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

        plugin_conf = lyrebird.context.application.conf.get('plugin.ios', {})
        default_bundle_id = plugin_conf.get('bundle_id', '')
        device_info['app'] = device.get_app_info(default_bundle_id)
        return jsonify(device_info)
    
    def conf(self):
        plugin_conf = lyrebird.context.application.conf.get('plugin.ios', {})
        default_bundle_id = plugin_conf.get('bundle_id', '')
        return jsonify({"bundleId": default_bundle_id})
        
    def device_list(self):
        return jsonify(device_service.devices_to_dict())

    def device_detail(self, device_id):
        return "\n".join(device_service.devices.get(device_id).device_info)

    def get_app_info(self, device_id, bundle_id):
        device = device_service.devices.get(device_id)
        def send_device_event():
            device_service.publish_devices_info_event(device, bundle_id)
        lyrebird.add_background_task('SendDeviceEvent', send_device_event)
        return jsonify(device.get_app_info(bundle_id))

    def app_list(self, device_id):
        device = device_service.devices.get(device_id)
        if device:
            app_list = device.get_apps_list(device_id)
            return jsonify(app_list)
        else:
            return context.make_fail_response('No device_id found.')
    
    def start_app(self, device_id, bundle_id):
        device = device_service.devices.get(device_id)
        port = lyrebird.context.application.conf.get('mock.port')
        res = device.start_app(bundle_id, get_ip(), port)
        if 'ConnectionResetError' in res and '54' in res:
            return context.make_fail_response('WDA is not ready!')
        return context.make_ok_response()

    def stop_app(self, device_id, bundle_id):
        device = device_service.devices.get(device_id)
        res = device.stop_app()
        if 'NoneType' in res:
            return context.make_fail_response('Cannot stop app before start it.')
        return context.make_ok_response()

    def logcat_start(self, device_id):
        print('Logcat start', device_id)
        device_service.start_log_recorder(device_id)

    def take_screen_shot(self, device_id):
        device = device_service.devices.get(device_id)
        img_info = device.take_screen_shot()
        timestrap = img_info.get('timestrap')
        if img_info.get('screen_shot_file'):
            test = {'imgUrl': f'/ui/plugin/iOS/api/src/screenshot/{device_id}?time={timestrap}'}
            return jsonify(test)
        else:
            return context.make_fail_response('Could not start screenshot service! '
                                              'Please make sure the idevicescreenshot command works correctly')

    def get_screen_shot(self, message):
        if message.get('cmd') != 'screenshot':
            return
        screen_shots = []
        device_list = message.get('device_id')
        for device_id in device_list:
            device = device_service.devices.get(device_id)
            if not device:
                continue
            screen_shot_info = device.take_screen_shot()
            screen_shots.append(
                {
                    'id': device_id,
                    'screenshot': {
                        'name': os.path.basename(screen_shot_info.get('screen_shot_file')),
                        'path': screen_shot_info.get('screen_shot_file')
                    }
                }
            )
        lyrebird.publish('ios.screenshot', screen_shots, state=True)

    def get_screenshot_image(self, device_id):
        if request.args.get('time'):
            model = device_service.devices.get(device_id).model.replace(' ', '_')
            timestrap = request.args.get('time')
            return send_from_directory(screenshot_dir, f'{model}_{timestrap}.png')
        else:
            return None

    def make_dump_data(self, path):
        device_data = {}
        device_data['name'] = os.path.basename(path)
        device_data['path'] = path
        return device_data

    def get_prop_file_path(self, device, device_id):
        device_prop_file_path = os.path.abspath(os.path.join(tmp_dir, '%s.info.txt' % device_id))
        device_prop = device.device_info
        device_prop_file = codecs.open(device_prop_file_path, 'w', 'utf-8')
        for prop_line in device_prop:
            device_prop_file.write(prop_line+'\n')
        device_prop_file.close()

        return device_prop_file_path

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
        # 获取设备列表
        self.add_url_rule('/api/devices', view_func=self.device_list)
        # 设备详情
        self.add_url_rule('/api/device/<string:device_id>', view_func=self.device_detail)
        # 获取app详情
        self.add_url_rule('/api/apps/<string:device_id>/<string:bundle_id>', view_func=self.get_app_info)
        # 进行截图
        self.add_url_rule('/api/screenshot/<string:device_id>', view_func=self.take_screen_shot)
        # 获取截图
        self.add_url_rule('/api/src/screenshot/<string:device_id>', view_func=self.get_screenshot_image)
        # 启动应用
        self.add_url_rule('/api/start_app/<string:device_id>/<string:bundle_id>', view_func=self.start_app)
        # 关闭应用
        self.add_url_rule('/api/stop_app/<string:device_id>/<string:bundle_id>', view_func=self.stop_app)
        # 获取设备应用列表
        self.add_url_rule('/api/apps/<string:device_id>', view_func=self.app_list)
        # 检查环境
        self.add_url_rule('/api/check-env', view_func=self.check_env)
        # 获取默认配置
        self.add_url_rule('/api/conf', view_func=self.conf) 
        # 启动设备监听服务
        lyrebird.start_background_task(device_service.run)
        # 订阅 cmd 消息，并开始截图
        lyrebird.subscribe('ios.cmd', self.get_screen_shot)

    @staticmethod
    def get_icon():
        # 设置插件 icon
        return 'fa fa-fw fa-apple'

    @staticmethod
    def get_title():
        # 设置插件的名称
        return 'iOS'


def get_ip():
    """
    获取当前设备在网络中的ip地址

    :return: IP地址字符串
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('google.com', 80))
    return s.getsockname()[0]
