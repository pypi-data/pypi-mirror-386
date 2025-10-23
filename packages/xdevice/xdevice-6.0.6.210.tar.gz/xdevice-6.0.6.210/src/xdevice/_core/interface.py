#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2020-2022 Huawei Device Co., Ltd.
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

from abc import ABC
from abc import abstractmethod
from enum import Enum
from typing import List

from _core.constants import DeviceProperties

__all__ = ["LifeCycle", "IDevice", "IDriver", "IListener", "IShellReceiver",
           "IParser", "ITestKit", "IScheduler", "IDeviceManager", "IReporter",
           "IFilter", "IProxy"]


class LifeCycle(Enum):
    TestTask = "TestTask"
    TestSuite = "TestSuite"
    TestCase = "TestCase"
    TestSuites = "TestSuites"


def _check_methods(class_info, *methods):
    mro = class_info.__mro__
    for method in methods:
        for cls in mro:
            if method in cls.__dict__:
                if cls.__dict__[method] is None:
                    return NotImplemented
                break
        else:
            return NotImplemented
    return True


class IDeviceManager(ABC):
    """
    Class managing the set of different types of devices for testing
    """
    __slots__ = ()
    support_labels = []
    support_types = []

    @abstractmethod
    def apply_device(self, device_option, timeout=10):
        pass

    @abstractmethod
    def release_device(self, device):
        pass

    @abstractmethod
    def reset_device(self, device):
        pass

    @classmethod
    def __subclasshook__(cls, class_info):
        if cls is IDevice:
            return _check_methods(class_info, "__serial__")
        return NotImplemented

    @abstractmethod
    def init_environment(self, environment, user_config_file):
        pass

    @abstractmethod
    def env_stop(self):
        pass

    @abstractmethod
    def list_devices(self):
        pass

    @staticmethod
    def init_devices_config(configs: dict, devices: List[dict], devices_sn_filter: List[str]):
        # devices的数据格式：[{"ip": "", "port": "", "sn": "", "alias": "", "reboot_timeout": ""}, ...]
        for device in devices:
            reboot_timeout = device.get(DeviceProperties.reboot_timeout, "").strip()
            try:
                if float(reboot_timeout) <= 0:
                    reboot_timeout = ""
            except ValueError:
                reboot_timeout = ""
            device.update({DeviceProperties.reboot_timeout: reboot_timeout})

            sn = device.get(DeviceProperties.sn)
            for s in sn.split(";"):
                s = s.strip()
                if s:
                    devices_sn_filter.append(s)
            if sn:
                configs.update({sn: device})
                continue
            if reboot_timeout:
                # 设备sn为空，reboot_timeout不为空，所有设备重启后的等待时长设为一样
                configs.update({DeviceProperties.reboot_timeout: reboot_timeout})


class IDevice(ABC):
    """
    IDevice provides a reliable and slightly higher level API to access
    devices
    """
    __slots__ = ()
    extend_value = {}
    env_index = None
    screenshot = False
    screenshot_fail = True
    
    @abstractmethod
    def __set_serial__(self, device_sn=""):
        pass

    @abstractmethod
    def __get_serial__(self):
        pass

    @abstractmethod
    def init_description(self):
        pass

    @classmethod
    def __subclasshook__(cls, class_info):
        if cls is IDevice:
            return _check_methods(class_info, "__serial__")
        return NotImplemented

    @abstractmethod
    def get(self, key=None, default=None):
        if not key:
            return default
        value = getattr(self, key, None)
        if value:
            return value
        else:
            return self.extend_value.get(key, default)

    @classmethod
    def check_advance_option(cls, extend_value, **kwargs):
        return True


class IDriver(ABC):
    """
    A test driver runs the tests and reports results to a listener.
    """
    __slots__ = ()

    @classmethod
    def __check_failed__(cls, msg):
        raise ValueError(msg)

    @abstractmethod
    def __check_environment__(self, device_options):
        """
        Check environment correct or not.
        You should return False when check failed.
        :param device_options:
        """

    @abstractmethod
    def __check_config__(self, config):
        """
        Check config correct or not.
        You should raise exception when check failed.
        :param config:
        """
        self.__check_failed__("Not implementation for __check_config__")

    @abstractmethod
    def __execute__(self, request):
        """
        Execute tests according to the request.
        """

    @classmethod
    def __dry_run_execute__(cls, request):
        """
        Dry run tests according to the request.
        """
        pass

    @abstractmethod
    def __result__(self):
        """
        Return tests execution result
        """

    @classmethod
    def __subclasshook__(cls, class_info):
        if cls is IDriver:
            return _check_methods(class_info, "__check_config__",
                                  "__execute__")
        return NotImplemented


class IScheduler(ABC):
    """
    A scheduler to run jobs parallel.
    """
    __slots__ = ()

    @abstractmethod
    def __discover__(self, args):
        """
        Discover tests according to request, and return root TestDescriptor.
        """

    @abstractmethod
    def __execute__(self, request):
        """
        Execute tests according to the request.
        """

    @classmethod
    @abstractmethod
    def __allocate_environment__(cls, options, test_driver):
        """
        Allocate environment according to the request.
        """

    @classmethod
    @abstractmethod
    def __free_environment__(cls, environment):
        """
        Free environment to the request.
        """

    @classmethod
    def __subclasshook__(cls, class_info):
        if cls is IScheduler:
            return _check_methods(class_info, "__discover__", "__execute__")
        return NotImplemented


class IListener(ABC):
    """
    Listener to be notified of test execution events by TestDriver, as
    following sequence:
    __started__(TestTask)
    __started__(TestSuite)
    __started__(TestCase)
    [__skipped__(TestCase)]
    [__failed__(TestCase)]
    __ended__(TestCase)
    ...
    [__failed__(TestSuite)]
    __ended__(TestSuite)
    ...
    [__failed__(TestTask)]
    __ended__(TestTask)
    """
    __slots__ = ()

    @abstractmethod
    def __started__(self, lifecycle, result):
        """
        Called when the execution of the TestCase or TestTask has started,
        before any test has been executed.
        """

    @abstractmethod
    def __ended__(self, lifecycle, result, **kwargs):
        """
        Called when the execution of the TestCase or TestTask has finished,
        after all tests have been executed.
        """

    @abstractmethod
    def __skipped__(self, lifecycle, result):
        """
        Called when the execution of the TestCase or TestTask has been skipped.
        """

    @abstractmethod
    def __failed__(self, lifecycle, result):
        """
        Called when the execution of the TestCase or TestTask has been skipped.
        """

    @classmethod
    def __subclasshook__(cls, class_info):
        if cls is IListener:
            return _check_methods(class_info, "__started__", "__ended__",
                                  "__skipped__", "__failed__")
        return NotImplemented


class IShellReceiver(ABC):
    """
    Read the output from shell out.
    """
    __slots__ = ()

    @abstractmethod
    def __read__(self, output):
        pass

    @abstractmethod
    def __error__(self, message):
        pass

    @abstractmethod
    def __done__(self, result_code, message):
        pass

    @classmethod
    def __subclasshook__(cls, class_info):
        if cls is IShellReceiver:
            return _check_methods(class_info, "__read__", "__error__",
                                  "__done__")
        return NotImplemented


class IParser(ABC):
    """
    A parser to parse the output of testcases.
    """
    __slots__ = ()

    @abstractmethod
    def __process__(self, lines):
        pass

    @abstractmethod
    def __done__(self):
        pass

    @classmethod
    def __subclasshook__(cls, class_info):
        if cls is IParser:
            return _check_methods(class_info, "__process__", "__done__")
        return NotImplemented


class ITestKit(ABC):
    """
    A test kit running on the host.
    """
    __slots__ = ()

    @classmethod
    def __check_failed__(cls, msg):
        raise ValueError(msg)

    @abstractmethod
    def __check_config__(self, config):
        """
        Check config correct or not.
        You should raise exception when check failed.
        :param config:
        """
        self.__check_failed__("Not implementation for __check_config__")

    @abstractmethod
    def __setup__(self, device, **kwargs):
        pass

    @abstractmethod
    def __teardown__(self, device):
        pass

    @classmethod
    def __subclasshook__(cls, class_info):
        if cls is ITestKit:
            return _check_methods(class_info, "__check_config__", "__setup__",
                                  "__teardown__")
        return NotImplemented


class IReporter(ABC):
    """
    A reporter to generate reports
    """
    __slots__ = ()

    @abstractmethod
    def __generate_reports__(self, report_path, **kwargs):
        pass

    @classmethod
    def __subclasshook__(cls, class_info):
        if cls is IReporter:
            return _check_methods(class_info, "__generate_reports__")
        return NotImplemented


class IProxy(ABC):
    """
    An extension plug-in used to extend device capabilities.
    """
    __slots__ = ()

    @abstractmethod
    def __set_device__(self, device):
        pass

    @abstractmethod
    def __init_proxy__(self):
        pass

    @abstractmethod
    def __reconnect_proxy__(self):
        pass

    @abstractmethod
    def __clean_proxy__(self):
        pass

    @classmethod
    def __subclasshook__(cls, class_info):
        if cls is IReporter:
            return _check_methods(class_info, "__set_device__", "__init_proxy__", "__reconnect_proxy__",
                                  "__clean_proxy__")
        return NotImplemented


class IFilter(ABC):
    """
    A filter is used to filter xml node and selector on the manager
    """
    __slots__ = ()

    @abstractmethod
    def __filter_xml_node__(self, node):
        pass

    @abstractmethod
    def __filter_selector__(self, selector):
        pass
