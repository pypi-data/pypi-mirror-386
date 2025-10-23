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

import copy
import os
import sys

from xdevice import HostDrivenTestType
from xdevice import ModeType
from xdevice import DeviceError
from xdevice import LiteDeviceError
from xdevice import ParamError
from xdevice import ReportException
from xdevice import ExecuteTerminate
from xdevice import IDriver
from xdevice import platform_logger
from xdevice import Plugin
from xdevice import JsonParser
from xdevice import get_config_value
from xdevice import do_module_kit_teardown
from xdevice import get_filename_extension
from xdevice import get_file_absolute_path
from xdevice import get_kit_instances
from xdevice import check_result_report
from xdevice import check_mode
from xdevice import SuiteReporter
from devicetest.error import ErrorMessage

LOG = platform_logger("WindowsTest")
PY_SUFFIX = ".py"
PYD_SUFFIX = ".pyd"


@Plugin(type=Plugin.DRIVER, id=HostDrivenTestType.windows_test)
class WindowsTestDriver(IDriver):
    """
    DeviceTest is a Test that runs a host-driven test on given devices.
    """
    # test driver config
    config = None
    result = ""
    error_message = ""
    py_file = ""

    def __init__(self):
        self.linux_host = ""
        self.linux_directory = ""
        self.hilog_file_pipes = []

    def __check_environment__(self, device_options):
        pass

    def __check_config__(self, config=None):
        pass

    def __init_nfs_server__(self, request=None):
        pass

    def __execute__(self, request):
        try:
            # set self.config
            self.config = request.config
            # get source, json config and kits
            if request.get_config_file():
                source = request.get_config_file()
                LOG.debug("Test config file path: %s" % source)
            else:
                source = request.get_source_string()
                LOG.debug("Test String: %s" % source)

            if not source:
                err_msg = ErrorMessage.TestCase.Code_0203010.format(request.get_source_file())
                LOG.error(err_msg)
                raise ParamError(err_msg)

            json_config = JsonParser(source)
            kits = get_kit_instances(json_config, request.config.resource_path,
                                     request.config.testcases_path)

            test_name = request.get_module_name()

            repeat = request.config.repeat
            repeat_round = request.get_repeat_round()
            round_folder = f"round{repeat_round}" if repeat > 1 else ""
            self.result = os.path.join(request.config.report_path, "result", round_folder, "{}.xml".format(test_name))

            # set configs keys
            configs = self._set_configs(json_config, kits, request)

            # get test list
            test_list = self._get_test_list(json_config, request, source)
            if not test_list:
                raise ParamError(ErrorMessage.TestCase.Code_0203011)
            self._run_devicetest(configs, test_list)
        except (ReportException, ModuleNotFoundError, ExecuteTerminate,
                SyntaxError, ValueError, AttributeError, TypeError,
                KeyboardInterrupt, ParamError, DeviceError, LiteDeviceError) \
                as exception:
            error_no = getattr(exception, "error_no", "00000")
            LOG.exception(exception, exc_info=False, error_no=error_no)
            self.error_message = exception

        finally:
            self._handle_finally(request)

    def _get_test_list(self, json_config, request, source):
        test_list = get_config_value('py_file', json_config.get_driver(),
                                     is_list=True)
        if str(request.root.source.source_file).endswith(PYD_SUFFIX) or \
                str(request.root.source.source_file).endswith(PY_SUFFIX):
            test_list = [request.root.source.source_file]

        if not test_list and os.path.exists(source):
            dir_name, file_name = os.path.split(source)
            file_name, _ = os.path.splitext(file_name)
            test_list = _get_dict_test_list(os.path.dirname(source), file_name)

        # check test list
        testcase = request.get("testcase")
        testcase_list = []
        if testcase:
            testcase_list = str(testcase).split(";")

        checked_test_list = []
        for _, test in enumerate(test_list):
            if not os.path.exists(test):
                try:
                    absolute_file = get_file_absolute_path(test, [
                        self.config.resource_path, self.config.testcases_path])
                except ParamError as error:
                    LOG.error(error, error_no=error.error_no)
                    continue
            else:
                absolute_file = test

            file_name = get_filename_extension(absolute_file)[0]
            if not testcase_list or file_name in testcase_list:
                checked_test_list.append(absolute_file)
            else:
                LOG.info("Test '%s' is ignored", absolute_file)
        if checked_test_list:
            LOG.info("Test list: {}".format(checked_test_list))
        else:
            raise ParamError(ErrorMessage.TestCase.Code_0203012)
        if len(checked_test_list) > 1:
            raise ParamError(ErrorMessage.TestCase.Code_0203013.format(request.get_module_name(), test_list))
        return checked_test_list

    def _set_configs(self, json_config, kits, request):
        configs = dict()
        configs["testargs"] = self.config.testargs or {}
        configs["testcases_path"] = self.config.testcases_path or ""
        configs["request"] = request
        configs["test_name"] = request.get_module_name()
        configs["report_path"] = request.config.report_path
        configs["execute"] = get_config_value(
            'execute', json_config.get_driver(), False)
        configs["listeners"] = request.listeners.copy()
        return configs

    def _handle_finally(self, request):
        from xdevice import Binder

        # do kit teardown
        do_module_kit_teardown(request)

        # check result report
        report_name = request.root.source.test_name if \
            not request.root.source.test_name.startswith("{") \
            else "report"
        module_name = request.get_module_name()
        if Binder.session().mode != ModeType.decc:
            self.result = check_result_report(
                request.config.report_path, self.result, self.error_message,
                report_name, module_name)
        else:
            tmp_list = copy.copy(SuiteReporter.get_report_result())
            if self.result not in [report_path for report_path, _ in tmp_list]:
                if not self.error_message:
                    self.error_message = "Case not execute[01205]"
                self.result = check_result_report(
                    request.config.report_path, self.result,
                    self.error_message, report_name, module_name)

    def _create_tmp_folder(self, request):
        if request.root.source.source_file.strip():
            folder_name = "task_%s_%s" % (self.config.tmp_id,
                                          request.root.source.test_name)
        else:
            folder_name = "task_%s_report" % self.config.tmp_id

        tmp_sub_folder = os.path.join(self.config.tmp_folder, folder_name)
        os.makedirs(tmp_sub_folder, exist_ok=True)
        return tmp_sub_folder

    def _run_devicetest(self, configs, test_list):
        from xdevice import Variables

        # insert paths for loading _devicetest module and testcases
        devicetest_module = os.path.join(Variables.modules_dir, "_devicetest")
        if os.path.exists(devicetest_module):
            sys.path.insert(1, devicetest_module)
        if configs["testcases_path"]:
            sys.path.insert(1, configs["testcases_path"])

        # apply data to devicetest module about resource path
        request = configs.get('request', None)
        if request:
            sys.ecotest_resource_path = request.config.resource_path

        # run devicetest
        from devicetest.main import DeviceTest
        device_test = DeviceTest(test_list, configs, [])
        device_test.run()

    def __result__(self):
        if check_mode(ModeType.decc):
            return self.result
        return self.result if os.path.exists(self.result) else ""


def _get_dict_test_list(module_path, file_name):
    test_list = []
    for root, _, files in os.walk(module_path):
        for _file in files:
            if (_file.endswith(".py") or _file.endswith(".pyd")) \
                    and file_name == os.path.splitext(_file)[0]:
                test_list.append(os.path.join(root, _file))
    return test_list
