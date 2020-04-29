from lyrebird.plugins import manifest
from . import apis

manifest(
    id='ios',
    name='iOS',
    api=[
        # get devices
        ('/api/devices', apis.device_list, ['GET']),
        # get device information
        ('/api/device/<string:device_id>', apis.device_detail, ['GET']),
        # get application information
        ('/api/apps/<string:device_id>/<string:bundle_id>', apis.get_app_info, ['GET']),
        # take screenshot
        ('/api/screenshot/<string:device_id>', apis.take_screen_shot, ['GET']),
        # get screenshot
        ('/api/src/screenshot/<string:device_id>', apis.get_screenshot_image, ['GET']),
        # start applicaton
        ('/api/start_app/<string:device_id>/<string:bundle_id>', apis.start_app, ['GET']),
        # stop application
        ('/api/stop_app/<string:device_id>/<string:bundle_id>', apis.stop_app, ['GET']),
        # get application list
        ('/api/apps/<string:device_id>', apis.app_list, ['GET']),
        # environment check
        ('/api/check_env', apis.check_env, ['GET']),
        # get config
        ('/api/conf', apis.conf, ['GET'])
    ],
    background=[
        ('ios_device_service', apis.device_service.run)
    ],
    event=[
        ('ios.cmd', apis.get_screen_shot)
    ]
)
