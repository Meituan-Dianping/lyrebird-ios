import os
import socket
import lyrebird
from flask import request, jsonify, send_from_directory
from lyrebird import application
from lyrebird.mock.context import make_ok_response, make_fail_response
from .device_service import DeviceService

device_service = DeviceService()
storage = lyrebird.get_plugin_storage()
screenshot_dir = os.path.abspath(os.path.join(storage, 'screenshot'))

def conf():
    plugin_conf = application.config.get('plugin.ios', {})
    default_bundle_id = plugin_conf.get('bundle_id', '')
    return make_ok_response(bundle_id=default_bundle_id)

def device_list():
    device_list = device_service.devices_to_dict()
    return make_ok_response(device_list=device_list)

def device_detail(device_id):
    device = device_service.devices.get(device_id)
    device_detail = '\n'.join(device.device_info)
    return make_ok_response(device_detail=device_detail)

def get_app_info(device_id, bundle_id):
    def send_device_event():
        device_service.publish_devices_info_event(device_service.devices, bundle_id)
    lyrebird.add_background_task('SendDeviceEvent', send_device_event)

    device = device_service.devices.get(device_id)
    app_info = device.get_app_info(bundle_id)
    return make_ok_response(app_info=app_info)

def app_list(device_id):
    device = device_service.devices.get(device_id)
    if device:
        app_list = device.get_apps_list(device_id)
        return make_ok_response(app_list=app_list)
    else:
        return make_fail_response(f'Device id {device_id} not found!')

def start_app(device_id, bundle_id):
    device = device_service.devices.get(device_id)
    port = application.config.get('mock.port')
    res = device.start_app(bundle_id, _get_ip(), port)
    if res:
        return make_fail_response(res)
    return make_ok_response()

def stop_app(device_id, bundle_id):
    device = device_service.devices.get(device_id)
    res = device.stop_app()
    if 'NoneType' in res:
        return make_fail_response(f'Cannot stop app {bundle_id} before start it')
    return make_ok_response()

def logcat_start(device_id):
    print('Logcat start', device_id)
    device_service.start_log_recorder(device_id)

def take_screen_shot(device_id):
    device = device_service.devices.get(device_id)
    img_info = device.take_screen_shot()
    if img_info['returncode'] != 0:
        return make_fail_response(img_info['result'].stdout.decode())
    timestamp = img_info.get('timestamp')
    return make_ok_response(imgUrl=f'/plugins/ios/api/src/screenshot/{device_id}?time={timestamp}')

def get_screen_shot(message):
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

def get_screenshot_image(device_id):
    if request.args.get('time'):
        model = device_service.devices.get(device_id).model.replace(' ', '_')
        timestamp = request.args.get('time')
        return send_from_directory(screenshot_dir, f'{model}_{timestamp}.png')
    else:
        return None

def check_env():
    msg = device_service.check_env()
    if device_service.status == device_service.RUNNING:
        return make_ok_response()
    else:
        return make_fail_response(msg)


def _get_ip():
    """
    Get ip address

    :return: IP
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('bing.com', 80))
    return s.getsockname()[0]
