# Lyrebird iOS Plugin

[![Build Status](https://travis-ci.org/Meituan-Dianping/lyrebird-ios.svg?branch=master)](https://travis-ci.org/Meituan-Dianping/lyrebird-ios)
[![PyPI](https://img.shields.io/pypi/v/lyrebird-ios.svg)](https://pypi.python.org/pypi/lyrebird-ios)
![PyPI](https://img.shields.io/pypi/pyversions/lyrebird-ios.svg)
![GitHub](https://img.shields.io/github/license/meituan/lyrebird-ios.svg)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/25eaa2cd08a34cad966a271cf0c2f910)](https://www.codacy.com/manual/Lyrebird/lyrebird-ios?utm_source=github.com&utm_medium=referral&utm_content=Meituan-Dianping/lyrebird-ios&utm_campaign=Badge_Grade)

---

**[Lyrebird](https://github.com/Meituan-Dianping/lyrebird)**
是一个基于拦截以及模拟 HTTP/HTTPs 网络请求的面向移动应用的插件化测试平台。

**iOS plugin 是一个 Lyrebird 的插件，用于从 iOS 设备获取信息，如详细的设备信息、屏幕快照和应用信息。**

## 快速开始

### 环境要求

- macOS

- [Python >= 3.6](https://www.python.org/downloads/release/python-360/)

- [libimobiledevice](https://github.com/libimobiledevice/libimobiledevice)

- [Command Line Tools for Xcode](https://developer.apple.com/download/more/)

### 环境准备

本插件依赖于 libimobiledevice 第三方依赖

1. 安装源管理工具 [Homebrew](https://brew.sh/)

1. 通过 Homebrew 安装 [libimobiledevice](https://github.com/libimobiledevice/libimobiledevice)

   ```bash
   brew install --HEAD libimobiledevice
   brew install ideviceinstaller
   brew link --overwrite libimobiledevice
   sudo chmod -R 777 /var/db/lockdown/
   ```

1. 最终，测试第三方依赖是否正常工作

   ```bash
   ideviceinfo
   idevicescreenshot
   ideviceinstaller -l
   ```

### 安装

```bash
pip3 install lyrebird-ios
```

### 启动

```bash
lyrebird
```

### 使用

使用时，通过 USB 线链接手机和电脑即可。

![Home Page](./image/iOS.png)

- 查看已连接设备的详细信息

- 截取 iOS 设备屏幕快照

- 查看已连接设备的应用信息

---

## 开发者指南

### 开发者环境

- macOS

- Python3.6 及以上

- NodeJS

- vscode(推荐)

- Chrome(推荐)

### 配置 Lyrebird-ios 工程

```bash
# clone 代码
git clone git@github.com:Meituan-Dianping/lyrebird-ios.git

# 进入工程目录
cd lyrebird-ios

# 初始化后端开发环境
python3 -m venv --clear venv

# 初始化前端开发环境
cd frontend
npm install
cd ..

# 使用IDE打开工程（推荐vscode）
code .
```

### 调试代码

#### Vscode debug 配置

```JSON
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "backend",
            "type": "python",
            "request": "launch",
            "module": "lyrebird",
            "console": "integratedTerminal",
            "args": [
                "-vv",
                "--plugin",
                "${workspaceFolder}"
            ]
        },
        {
            "name": "frontend",
            "type": "chrome",
            "request": "launch",
            "url": "http://localhost:8080/ui/static/",
            "webRoot": "${workspaceFolder}/frontend/src/",
            "breakOnLoad": true,
            "sourceMapPathOverrides": {
              "webpack:///src/*": "${webRoot}/*"
            }
        }
    ]
}
```

#### 后端代码

1. 激活 python 虚拟环境

   通过 `source venv/bin/activate` 激活虚拟环境

2. 通过 Debug 功能启动

   按照上面 debug 配置中 python:Lyrebrid 配置启动即可

#### 前端代码

1. 启动 node server

```bash
# 进入前端目录
cd frontend

# 启动前端node serve
npm run serve
```

2. 通过 Debug 功能启动浏览器

   按照上面 debug 配置中 vuejs: chrome 配置启动即可

   > 注意: vscode 需要安装 chrome debug 插件

3. build 前端项目

```bash
# 进入前端目录
cd frontend

# build前端
npm run build
```

## 常见问题

#### libimobiledevice 无法使用，终端提示 - "Could not connect to lockdownd ...".

按照如下步骤重新安装 libimobiledevice，并留意安装过程中的错误提示。

1. 卸载 libimobiledevice

   ```
   brew uninstall --ignore-dependencies libimobiledevice
   ```

1. 安装 libimobiledevice

   ```
   brew install --HEAD libimobiledevice
   ```

1. 若在安装 libimobiledevice 时出现了错误提示，如提示 usbmuxd 的版本不正确，使用如下命令解决依赖的版本问题

   ```
   brew uninstall --ignore-dependencies usbmuxd
   brew install --HEAD usbmuxd
   brew unlink usbmuxd
   brew link usbmuxd
   ```

1. 再次安装 libimobiledevice

   ```
   brew install --HEAD libimobiledevice
   ```

#### 截取屏幕快照功能无法正常工作，提示 Could not start screenshot service!

在连接设备之前您必须确保开发者选项可用。通过 [stackoverflow](https://stackoverflow.com/questions/30736932/xcode-error-could-not-find-developer-disk-image) 获取更多解决帮助。
