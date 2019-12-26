from lyrebird.plugins import manifest
from . import apis

manifest(
    id='ios',
    name='iOS',
    api=[
        # 获取设备列表
        ('/api/devices', apis.device_list, ['GET']),
        # 设备详情
        ('/api/device/<string:device_id>', apis.device_detail, ['GET']),
        # 获取app详情
        ('/api/apps/<string:device_id>/<string:bundle_id>', apis.get_app_info, ['GET']),
        # 进行截图
        ('/api/screenshot/<string:device_id>', apis.take_screen_shot, ['GET']),
        # 获取截图
        ('/api/src/screenshot/<string:device_id>', apis.get_screenshot_image, ['GET']),
        # 启动应用
        ('/api/start_app/<string:device_id>/<string:bundle_id>', apis.start_app, ['GET']),
        # 关闭应用
        ('/api/stop_app/<string:device_id>/<string:bundle_id>', apis.stop_app, ['GET']),
        # 获取设备应用列表
        ('/api/apps/<string:device_id>', apis.app_list, ['GET']),
        # 检查环境
        ('/api/check-env', apis.check_env, ['GET']),
        # 获取默认配置
        ('/api/conf', apis.conf, ['GET'])
    ],
    background=[
        ('ios_device_service', apis.device_service.run)
    ],
    event=[
        ('ios.cmd', apis.get_screen_shot)
    ]
)
