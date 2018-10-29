import lyrebird
from lyrebird import context
from . import ios_helper
from lyrebird.log import get_logger

_log = get_logger()


class DeviceService:
    """
    设备服务 manager
    """
    READY = 0
    RUNNING = 1
    STOP = 2

    def __init__(self):
        self.status = self.READY
        self.handle_interval = 1
        self.devices = {}
        print('DeviceService OnCreate')

    def devices_to_dict(self):
        json_obj = {}
        for device_id in self.devices:
            json_obj[device_id] = self.devices[device_id].to_dict()
        return json_obj

    def run(self):
        self.status = self.RUNNING
        print('iOS device listener start')
        while self.status == self.RUNNING:
            try:
                self.handle()
                context.application.socket_io.sleep(self.handle_interval)
            except Exception as e:
                _log.error(e)
        self.status = self.STOP
        print('iOS device listener stop')

    def handle(self):
        devices = ios_helper.devices()
        if len(devices) == len(self.devices):
            if len([k for k in devices if k not in self.devices]) == 0:
                return

        self.devices = devices
        self.publish_devices_info_event(self.devices, self.get_default_app_name())
        context.application.socket_io.emit('device', namespace='/iOS-plugin')

    def start_log_recorder(self, device_id):
        for _device_id in self.devices:
            if _device_id == device_id:
                self.devices[_device_id].start_log()
            else:
                self.devices[_device_id].stop_log()

    def publish_devices_info_event(self, online_devices, app_name):
        devices = []
        for item in online_devices:
            device_info = online_devices[item]
            app_info = online_devices[item].get_app_info(app_name)
            message_info = {
                'id': device_info.device_id,
                'info': {
                    'name': device_info.device_name,
                    'model': device_info.model,
                    'os': device_info.os_version,
                    'sn': device_info.sn
                },
            }
            if app_info.get('AppName'):
                message_info['app'] = {
                    'name': app_info['AppName'],
                    'version': app_info['VersionNumber'],
                    'build': app_info['BuildNumber'],
                    'bundleID': app_info['BundleID']
                }
            devices.append(message_info)
        lyrebird.publish('ios.device', devices, state=True)

    @staticmethod
    def get_default_app_name():
        plugin_conf = lyrebird.context.application.conf.get('plugin.ios', {})
        default_bundle_id = plugin_conf.get('bundle_id', '')
        return default_bundle_id
