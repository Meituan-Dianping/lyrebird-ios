from lyrebird import context
from . import ios_helper
from lyrebird.mock.logger_helper import get_logger

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
        context.application.socket_io.emit('device', namespace='/iOS-plugin')

    def start_log_recorder(self, device_id):
        for _device_id in self.devices:
            if _device_id == device_id:
                self.devices[_device_id].start_log()
            else:
                self.devices[_device_id].stop_log()
