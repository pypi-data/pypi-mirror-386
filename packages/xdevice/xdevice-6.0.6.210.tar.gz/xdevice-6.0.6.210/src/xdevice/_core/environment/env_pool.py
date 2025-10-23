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
import json
import os
import time
import sys

from abc import abstractmethod
from abc import ABCMeta
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from _core.analysis.tracker import TrackEvent, Tracker
from _core.interface import IFilter
from _core.interface import IDeviceManager
from _core.logger import platform_logger
from _core.plugin import Plugin
from _core.plugin import get_plugin
from _core.utils import convert_serial
from _core.utils import get_cst_time
from _core.logger import change_logger_level
from _core.constants import ConfigConst
from _core.constants import FilePermission
from _core.context.log import RuntimeLogs

LOG = platform_logger("EnvPool")

__all__ = ["EnvPool", "XMLNode", "Selector", "DeviceSelector", "DeviceNode", "is_env_pool_run_mode"]


class EnvPool(object):
    """
    Class representing environment pool that
    managing the set of available devices for testing.
    this class is used directly by users without going through the command flow.
    """
    instance = None
    __init_flag = False
    report_path = None
    resource_path = None
    generate_report = True

    def __new__(cls, *args, **kwargs):
        """
        Singleton instance
        """
        del args, kwargs
        if cls.instance is None:
            cls.instance = super(EnvPool, cls).__new__(cls)
        return cls.instance

    def __init__(self, **kwargs):
        event = TrackEvent.TestTaskDebug
        Tracker.event(event.value, event_name=event.name)
        EnvPool.report_path = kwargs.get("report_path", "")
        EnvPool.generate_report = kwargs.get("generate_report", True)
        self._stop_task_log()
        self._start_task_log()
        if EnvPool.__init_flag:
            return
        self._managers = {}
        self._filters = {}
        self._init_log_level(kwargs.get("log_level", "info"))
        self._load_managers()
        EnvPool.__init_flag = True
        EnvPool.resource_path = kwargs.get("resource_path",
                                           os.path.join(os.path.abspath(os.getcwd()), "resource"))
        setattr(sys, "ecotest_resource_path", EnvPool.resource_path)
        # init cache file and check if expire
        cache_file = Cache()
        cache_file.check_cache_if_expire()
        self.devices = list()

    def _load_managers(self):
        LOG.info("Load Managers ...")
        from xdevice import EnvironmentManager
        # 通过_EnvironmentManager__init_flag、_EnvironmentManager__instance访问私有属性
        if EnvironmentManager._EnvironmentManager__init_flag:
            LOG.info("The environment manager has been initialized, and we need to reinitialize it "
                     "to ensure that the device is properly initialized")
            env_manager = EnvironmentManager()
            env_manager.env_stop()
            time.sleep(3)
        manager_plugins = get_plugin(Plugin.MANAGER)
        for manager_plugin in manager_plugins:
            manager_name = manager_plugin.__class__.__name__
            if manager_name in self._managers:
                continue
            try:
                manager_instance = manager_plugin.__class__()
                self._managers[manager_name] = manager_instance
            except Exception as error:
                LOG.error("Pool start error: {}".format(error))
        # 倒序排列, 优先加载OH设备
        if self._managers:
            self._managers = dict(sorted(self._managers.items(), reverse=True))

    def _unload_manager(self):
        for manager in self._managers.values():
            if manager.__class__.__name__ not in self._filters:
                continue
            manager.devices_list.clear()
            manager.env_stop()
        self._managers.clear()
        EnvPool.__init_flag = False

    def get_device(self, selector, timeout=10):
        LOG.info("Get device by selector")
        device = self._apply_device(selector, timeout)
        if device is not None:
            LOG.info("Device {}: extend value: {}".format(
                convert_serial(device.device_sn), device.extend_value))
            self.devices.append(device)
        else:
            LOG.info("Require label is '{}', can't get device".
                     format(selector.label))
        return device

    def init_pool(self, node):
        LOG.info("Prepare to init pool")
        for manager in self._managers.values():
            if not isinstance(manager, IFilter):
                continue
            # node，传入格式化的环境配置信息，按需初始化设备管理器和测试设备
            environment = node
            if isinstance(node, DeviceNode):
                if not manager.__filter_xml_node__(node):
                    continue
                environment = node.format()
            if not isinstance(manager, IDeviceManager):
                continue
            manager.init_environment(environment, "")
            self._filters[manager.__class__.__name__] = manager
            LOG.info("Pool is prepared")
        if not self._filters:
            LOG.info("Can't find any manager, may be no connector are assign"
                     "or the plugins of manager are not installed!")

    def shutdown(self):
        # clear device rpc port
        for device in self.devices:
            if hasattr(device, "remove_ports"):
                device.remove_ports()
        self._unload_manager()
        self._stop_task_log()
        EnvPool.instance = None
        EnvPool.__init_flag = False

    def _apply_device(self, selector, timeout=3):
        LOG.info("Apply device in pool")
        for manager_type, manager in self._filters.items():
            if not manager.__filter_selector__(selector):
                continue
            device_option = selector.format()
            if not device_option:
                continue
            support_labels = getattr(manager, "support_labels", [])
            support_types = getattr(manager, "support_types", [])
            if device_option.required_manager not in support_types:
                LOG.info("'{}' not in {}'s support types".format(
                    device_option.required_manager, manager_type))
                continue
            if not support_labels:
                continue
            if device_option.label is None:
                skip_rules = [manager_type != "ManagerDevice"]
                if all(skip_rules):
                    continue
            else:
                if support_labels and \
                        device_option.label not in support_labels:
                    continue
            device = manager.apply_device(device_option, timeout)
            if hasattr(device, "env_index"):
                device.env_index = device_option.get_env_index()
            if device:
                return device
        else:
            return None

    @classmethod
    def _init_log_level(cls, level):
        if str(level).lower() not in ["debug", "info"]:
            LOG.info("Level str must be 'debug' or 'info'")
            return
        change_logger_level({"console": level})

    @classmethod
    def _start_task_log(cls):
        if not EnvPool.generate_report:
            return
        report_folder_path = EnvPool.report_path
        if not report_folder_path:
            report_folder_path = os.path.join(
                os.path.abspath(os.getcwd()), "reports", get_cst_time().strftime("%Y-%m-%d-%H-%M-%S"))
        if not os.path.exists(report_folder_path):
            os.makedirs(report_folder_path)
        LOG.info("Report path: {}".format(report_folder_path))
        EnvPool.report_path = report_folder_path
        RuntimeLogs.start_task_log(report_folder_path)

    @classmethod
    def _stop_task_log(cls):
        if not EnvPool.generate_report:
            return
        RuntimeLogs.stop_task_logcat()


class XMLNode(metaclass=ABCMeta):

    @abstractmethod
    def __init__(self):
        self.__device_ele = Element("device")
        self.__connectors = []

    @abstractmethod
    def __on_root_attrib__(self, attrib_dict):
        pass

    def add_element_string(self, element_str=""):
        if element_str:
            device_ele = ElementTree.fromstring(element_str)
            if device_ele.tag == "device":
                self.__device_ele = device_ele
        return self

    @classmethod
    def create_node(cls, tag):
        return Element(tag)

    def build_connector(self, connector_name):
        self.__connectors.append(connector_name)
        return self

    def get_connectors(self):
        return self.__connectors

    def format(self):
        attrib_dict = dict()
        self.__on_root_attrib__(attrib_dict)
        self.__device_ele.attrib = attrib_dict
        env = self.create_node("environment")
        env.append(self.__device_ele)
        root = self.create_node("user_config")
        root.append(env)
        return ElementTree.tostring(root, encoding="utf-8")

    def get_root_node(self):
        return self.__device_ele


class Selector(metaclass=ABCMeta):

    @abstractmethod
    def __init__(self, _type, label):
        self.__device_dict = dict()
        self.__config = dict()
        self.label = label
        self.type = _type

    def add_environment_content(self, content):
        _content = content
        if isinstance(_content, str):
            _content = _content.strip()
            if _content.startswith("[") and _content.endswith("]"):
                self.__device_dict.update(json.loads(_content)[0])
            elif _content.startswith("{") and _content.endswith("}"):
                self.__device_dict.update(json.loads(content))
            else:
                raise RuntimeError("Invalid str input! ['{}']".format(_content))
        elif isinstance(_content, list):
            self.__device_dict.update(_content[0])
        elif isinstance(_content, dict):
            self.__device_dict.update(_content)
        return self

    @abstractmethod
    def __on_config__(self, config, device_dict):
        pass

    @abstractmethod
    def __on_selection_option__(self, selection_option):
        pass

    def add_label(self, label):
        self.label = label
        return self

    def add_type(self, _type):
        self.type = _type
        return self

    def format(self):
        if self.type or self.label:
            self.__device_dict.update({"type": self.type})
            self.__device_dict.update({"label": self.label})
        self.__on_config__(self.__config, self.__device_dict)
        index = 1
        label = self.__device_dict.get("label", "phone")
        required_manager = self.__device_dict.get("type", "device")
        device_option = SelectionOption(self.__config, label)
        self.__device_dict.pop("type", None)
        self.__device_dict.pop("label", None)
        device_option.required_manager = required_manager
        device_option.extend_value = self.__device_dict
        if hasattr(device_option, "env_index"):
            device_option.env_index = index
        index += 1
        self.__on_selection_option__(device_option)
        self.__device_dict.clear()
        self.__config.clear()
        return device_option


class SelectionOption:
    def __init__(self, options, label=None):
        self.device_sn = [x for x in options["device_sn"].split(";") if x]
        self.label = label
        self.source_file = ""
        self.extend_value = {}
        self.required_manager = ""
        self.env_index = None

    def get_label(self):
        return self.label

    def get_env_index(self):
        return self.env_index

    def matches(self, device):
        LOG.info("Do matches, device:[state:{}, sn:{}, label:{}], selection "
                 "option:[device sn:{}, label:{}]".format(
                   device.device_allocation_state,
                   convert_serial(device.device_sn),
                   device.label,
                   [convert_serial(sn) if sn else "" for sn in self.device_sn],
                   self.label))
        if not getattr(device, "task_state", True):
            return False

        if len(self.device_sn) != 0 and device.device_sn not in self.device_sn:
            return False

        return True


class DeviceNode(XMLNode):

    def __init__(self, usb_type, label=""):
        super().__init__()
        self.usb_type = usb_type
        self.label = label
        self.get_root_node().append(self.create_node("sn"))
        self.get_root_node().append(self.create_node("ip"))
        self.get_root_node().append(self.create_node("port"))

    def __on_root_attrib__(self, attrib_dict):
        attrib_dict.update({"type": self.usb_type})
        if self.label:
            attrib_dict.update({"label": self.label})

    def add_address(self, host, port):
        host_ele = self.get_root_node().find("ip")
        port_ele = self.get_root_node().find("port")
        host_ele.text = host
        port_ele.text = port
        return self

    def add_device_sn(self, device_sn):
        sn_ele = self.get_root_node().find("sn")
        if sn_ele.text:
            sn_ele.text = "{};{}".format(sn_ele.text, device_sn)
        else:
            sn_ele.text = device_sn
        return self


class DeviceSelector(Selector):

    def __init__(self, _type="", label=""):
        super().__init__(_type, label)
        self.device_sn = ""

    def __on_config__(self, config, device_dict):
        config.update({"device_sn": self.device_sn})

    def __on_selection_option__(self, selection_option):
        pass

    def add_device_sn(self, device_sn):
        self.device_sn = device_sn
        return self


class Cache:
    def __init__(self):
        from xdevice import Variables
        self.cache_file = os.path.join(Variables.temp_dir, "cache.dat")
        self.expire_time = 1  # days

    def check_cache_if_expire(self):
        if os.path.exists(self.cache_file):
            current_modify_time = os.path.getmtime(self.cache_file)
            current_time = time.time()
            if Cache.get_delta_days(current_modify_time, current_time) < self.expire_time:
                setattr(sys, ConfigConst.env_pool_cache, True)
                LOG.info("Env pool running in cache mode.")
                return
        self.update_cache()
        setattr(sys, ConfigConst.env_pool_cache, False)
        LOG.info("Env pool running in normal mode.")

    @staticmethod
    def get_delta_days(t1, t2):
        import datetime
        dt2 = datetime.datetime.fromtimestamp(t2)
        dt1 = datetime.datetime.fromtimestamp(t1)
        return (dt2 - dt1).days

    def update_cache(self):
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        with os.fdopen(os.open(self.cache_file, flags, FilePermission.mode_755),
                       "wb") as f:
            f.write(b'123')  # 写入字节数据


def is_env_pool_run_mode():
    return False if EnvPool.instance is None else True
