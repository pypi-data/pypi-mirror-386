#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import time
import traceback
import json

from devicetest.core.variables import DeccVariable
from devicetest.log.logger import print_image, DeviceTestLog as log
from devicetest.utils.file_util import create_dir
from devicetest.utils.time_util import TimeHandler
from xdevice import stop_standing_subprocess
from xdevice import DeviceConnectorType
from xdevice import IDevice
from xdevice import TestDeviceState

LOCAL_IP = "127.0.0.1"
LOCAL_PORT = 6001
URL = "/"
FORWARD_PORT = 9501
SCREENRECORDER_COMMAND = "aa {} -b com.huawei.ohos.screenrecorder -a com.huawei.ohos.screenrecorder.ServiceExtAbility"


class ScreenAgent:
    SCREEN_AGENT_MAP = {}

    def __init__(self, device):
        self._device = device
        self.log = device.log
        self.proc = None
        self.thread = None
        self.local_port = None
        self.is_server_started = False

    def __del__(self):
        self.terminate()

    @classmethod
    def get_instance(cls, _device):
        _device.log.debug("in get instance.")
        instance_sn = _device.device_sn
        if instance_sn in ScreenAgent.SCREEN_AGENT_MAP:
            return ScreenAgent.SCREEN_AGENT_MAP[instance_sn]

        agent = ScreenAgent(_device)
        ScreenAgent.SCREEN_AGENT_MAP[instance_sn] = agent
        _device.log.debug("out get instance.")
        return agent

    @classmethod
    def remove_instance(cls, _device):
        _sn = _device.device_sn
        if _sn in ScreenAgent.SCREEN_AGENT_MAP:
            ScreenAgent.SCREEN_AGENT_MAP[_sn].terminate()
            del ScreenAgent.SCREEN_AGENT_MAP[_sn]

    @classmethod
    def add_step_screenshot(cls, link: str, title: str):
        """截图关联步骤（对外接口，勿删）
        link: 基于报告的截图相对路径
        title: 截图描述
        """
        cur_case = DeccVariable.cur_case()
        if cur_case:
            cur_case.update_step_shots(link, title)

    @classmethod
    def get_screenshot_dir(cls):
        cur_case = DeccVariable.cur_case()
        return cur_case.get_screenshot_dir() if cur_case else None

    @classmethod
    def get_take_picture_path(cls, _device, picture_name, ext=".png", exe_type="takeImage", is_collector=False):
        """新增参数exeType，默认值为takeImage;可取值takeImage/dumpWindow"""
        if os.path.isfile(picture_name):
            folder = os.path.dirname(picture_name)
            create_dir(folder)
            return picture_name, os.path.basename(picture_name)

        folder = cls.get_screenshot_dir()
        if is_collector:
            folder = os.path.join(folder, 'collector')
        create_dir(folder)
        if picture_name.endswith(ext):
            picture_name = picture_name.strip(ext)

        if exe_type == "takeImage":
            save_name = "{}.{}{}{}".format(
                _device.device_sn.replace("?", "sn").replace(":", "_"), picture_name,
                DeccVariable.cur_case().image_num, ext)
        elif exe_type == "videoRecord":
            save_name = "{}.{}{}{}".format(
                _device.device_sn.replace("?", "sn").replace(":", "_"), picture_name,
                DeccVariable.cur_case().video_num, ext)
        elif exe_type == "stepImage":
            save_name = "{}.{}{}".format(
                _device.device_sn.replace("?", "sn").replace(":", "_"), picture_name, ext)
        else:
            save_name = "{}.{}{}{}".format(
                _device.device_sn.replace("?", "sn").replace(":", "_"), picture_name,
                DeccVariable.cur_case().dump_xml_num, ext)

        fol_path = os.path.join(folder, save_name)
        if exe_type == "takeImage":
            DeccVariable.cur_case().image_num += 1
        elif exe_type == "videoRecord":
            DeccVariable.cur_case().video_num += 1
        else:
            if exe_type != "stepImage":
                DeccVariable.cur_case().dump_xml_num += 1
        return fol_path, save_name

    @classmethod
    def screen_take_picture(cls, args, result, _ta=None, is_raise_exception=True, screenshot: bool = True):
        # When the phone is off, you can set the screenshot off function
        # screenshot 由aw传入的忽略截图参数, 正常执行忽略截图, aw失败还是截图
        _ta = _ta or "stepepr"
        try:
            if len(args) == 0:
                return
            _device = args[0]
            if not isinstance(_device, IDevice):
                # 适配Hypium的AW接口
                for arg in args:
                    _d = getattr(arg, "_device", None)
                    if _d is not None:
                        _device = _d
                        break
            if not isinstance(_device, IDevice):
                log.debug("can not find device object from aw args")
                return
            # aw接口运行失败必须截图；每个aw接口运行都截图，需将screenshot设为true
            aw_screenshot = hasattr(_device, "screenshot") and _device.screenshot is True and screenshot
            if aw_screenshot:
                if not result:
                    _ta = f"{_ta}_fail"
            else:
                if not result and is_raise_exception:
                    _ta = f"{_ta}_fail"
                else:
                    # 未配置aw接口截图，且aw运行正常，则无需截图
                    return
            cls.screenshot(_device, _ta)
        except Exception as e:
            log.error(f"screen take picture error, {e}")
            log.debug(traceback.format_exc())

    @classmethod
    def screenshot(cls, device, title='', **kwargs):
        """设备截图（对外接口，勿删）
        device: 设备对象
        title : 截图信息
        """
        is_collector = kwargs.get('is_collector', False)
        ext = '.jpeg'
        file_name = TimeHandler.get_now_datetime()
        path, link = '', ''
        try:
            path, save_name = cls.get_take_picture_path(
                device, file_name, ext,
                exe_type='stepImage', is_collector=is_collector)
            case_name = DeccVariable.cur_case().get_current_case_name()
            if is_collector:
                link = os.path.join(case_name, 'collector', save_name)
            else:
                link = os.path.join(case_name, save_name)
            # 截图文件后缀在方法内可能发生更改
            path, link = cls._do_capture(device, link, path, title, ext)
        except Exception as e:
            log.error(f'take screenshot on step failed. {e}')
        if path and os.path.exists(path):
            cls.add_step_screenshot(link, title)
        return path, link.replace('\\', '/')

    @classmethod
    def _do_capture(cls, _device, link, path, title, ext=".png"):
        # 设备处于断开状态，打印提示信息
        if hasattr(_device, 'test_device_state') and _device.test_device_state != TestDeviceState.ONLINE:
            _device.log.debug("{} device is offline, status: {}".format(_device.device_sn, _device.test_device_state))
        try:
            if hasattr(_device, "capture"):
                # 截图需要设备对象实现capture方法
                display_id = 0
                hypium_config = getattr(_device, "_hypium_config", None)
                if hypium_config:
                    display_id = getattr(hypium_config, "default_display_id", 0)
                link, path = _device.capture(link, path, ext, display_id)
                # 压缩图片为80%
                cls.compress_image(path)
            else:
                _device.log.debug("The device not implement capture function, don't capture!")
            if path and link:
                print_image(link, path, title, cls.resize_image(path))
        except Exception as e:
            _device.log.warning("{} device capture failed: {}".format(_device.device_sn, e))
            return "", ""
        return path, link

    @classmethod
    def get_ui_step_picture(cls, file_name, _device, ext=".png"):
        """获取ui自适应截图需要移动的路径
        file_name: str, 保存的图片名称
        _device  : object, the device object to capture
        ext : str, 保存图片后缀,支持".png"、".jpg"格式
        """
        try:
            path, save_name = cls.get_take_picture_path(_device, file_name, ext, exe_type="stepImage")
            link = os.path.join(DeccVariable.cur_case().get_current_case_name(), save_name)
            # 截图文件后缀在方法内可能发生更改
            return path, link
        except Exception as e:
            log.error(f"take screenshot on step failed, reason: {e}")
        return '', ''


    @classmethod
    def compress_image(cls, img_path, ratio=0.5, quality=80):
        try:
            import cv2
            import numpy as np
            pic = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), -1)
            height, width, deep = pic.shape
            width, height = (width * ratio, height * ratio)
            pic = cv2.resize(pic, (int(width), int(height)))
            params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            cv2.imencode('.jpeg', pic, params=params)[1].tofile(img_path)
        except (ImportError, NameError):
            pass

    @classmethod
    def get_image_dir_path(cls, _device, name, ext=".png", exe_type="takeImage"):
        """
        增加了 exeType参数，默认为takeImage;可取值:takeImage/dumpWindow
        """
        try:
            if hasattr(_device, "is_oh") or hasattr(_device, "is_mac"):
                phone_time = _device.execute_shell_command("date '+%Y%m%d_%H%M%S'").strip()
            else:
                phone_time = _device.connector.shell("date '+%Y%m%d_%H%M%S'").strip()
        except Exception as exception:
            _device.log.error("get date exception error")
            _device.log.debug("get date exception: {}".format(exception))
        else:
            name = "{}.{}".format(phone_time, name)
        path, save_name = cls.get_take_picture_path(_device, name, ext, exe_type)
        link = os.path.join(DeccVariable.cur_case().get_current_case_name(), save_name)
        return path, link

    @classmethod
    def resize_image(cls, file_path, max_height=480, file_type="image"):
        width, height = 1080, 1920
        ratio = 1
        try:
            if os.path.exists(file_path):
                if file_type == "image":
                    from PIL import Image
                    img = Image.open(file_path)
                    width, height = img.width, img.height
                    img.close()
                elif file_type == "video":
                    import cv2
                    try:
                        video_info = cv2.VideoCapture(file_path)
                        width = int(video_info.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(video_info.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        video_info.release()
                    except Exception as e:
                        log.warning("get video width and height error: {}, use default".format(e))
                    if width == 0 or height == 0:
                        width, height = 1080, 1920
            if height < max_height:
                return 'width="%d" height="%d"' % (width, height)
            ratio = max_height / height
        except ImportError:
            log.error("Pillow or opencv-python is not installed ")
        except ZeroDivisionError:
            log.error("shot image height is 0")
        return 'width="%d" height="%d"' % (width * ratio, max_height)

    def terminate(self):
        if self.local_port is not None and isinstance(self.local_port, int):
            if hasattr(self._device, "is_oh") or \
                    self._device.usb_type == DeviceConnectorType.hdc:
                self._device.connector_command('fport rm tcp:{}'.format(self.local_port))
            else:
                self._device.connector_command('forward --remove tcp:{}'.format(self.local_port))
        if self.proc is not None:
            stop_standing_subprocess(self.proc)
        if self.thread is not None:
            start = time.time()
            # 任务结束要等图片生成完
            while self.thread.isAlive() and time.time() - start < 3:
                time.sleep(0.1)
