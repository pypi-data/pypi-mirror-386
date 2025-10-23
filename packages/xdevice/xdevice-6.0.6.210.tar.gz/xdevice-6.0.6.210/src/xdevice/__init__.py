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

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from _core.variables import Variables
from _core.plugin import Plugin
from _core.plugin import get_plugin
from _core.logger import platform_logger
from _core.logger import redirect_driver_log_begin
from _core.logger import redirect_driver_log_end
from _core.logger import get_driver_log_path
from _core.interface import IDriver
from _core.interface import IDevice
from _core.interface import IDeviceManager
from _core.interface import IFilter
from _core.interface import IParser
from _core.interface import LifeCycle
from _core.interface import IShellReceiver
from _core.interface import ITestKit
from _core.interface import IListener
from _core.interface import IReporter
from _core.interface import IProxy
from _core.exception import ParamError
from _core.exception import DeviceError
from _core.exception import LiteDeviceError
from _core.exception import ExecuteTerminate
from _core.exception import ReportException
from _core.exception import HdcError
from _core.exception import HdcCommandRejectedException
from _core.exception import ShellCommandUnresponsiveException
from _core.exception import DeviceUnresponsiveException
from _core.exception import AppInstallError
from _core.exception import RpcNotRunningError
from _core.exception import HapNotSupportTest
from _core.constants import DeviceTestType
from _core.constants import DeviceLabelType
from _core.constants import ManagerType
from _core.constants import DeviceOsType
from _core.constants import ProductForm
from _core.constants import TestType
from _core.constants import CKit
from _core.constants import ConfigConst
from _core.constants import ReportConst
from _core.constants import ModeType
from _core.constants import TestExecType
from _core.constants import ListenerType
from _core.constants import GTestConst
from _core.constants import CommonParserType
from _core.constants import FilePermission
from _core.constants import HostDrivenTestType
from _core.constants import DeviceConnectorType
from _core.constants import DeviceProperties
from _core.constants import AdvanceDeviceOption
from _core.constants import Platform
from _core.constants import HcpTestMode
from _core.constants import LifeStage
from _core.constants import AgentMode
from _core.config.config_manager import UserConfigManager
from _core.config.resource_manager import ResourceManager
from _core.error import Error
from _core.error import ErrorCategory
from _core.executor.abs import UniversalReportListener
from _core.executor.bean import CaseResult
from _core.executor.bean import SuiteResult
from _core.executor.bean import SuitesResult
from _core.executor.bean import StateRecorder
from _core.executor.listener import TestDescription
from _core.executor.listener import CollectingTestListener
from _core.executor.request import Request
from _core.executor.request import Task
from _core.testkit.json_parser import JsonParser
from _core.testkit.kit import junit_para_parse
from _core.testkit.kit import gtest_para_parse
from _core.testkit.kit import reset_junit_para
from _core.testkit.kit import get_app_name_by_tool
from _core.testkit.kit import get_install_args
from _core.testkit.kit import remount
from _core.testkit.kit import disable_keyguard
from _core.testkit.kit import unlock_screen
from _core.testkit.kit import unlock_device
from _core.testkit.kit import get_class
from _core.testkit.kit import check_device_ohca
from _core.testkit.kit import do_module_kit_setup
from _core.testkit.kit import do_module_kit_teardown
from _core.testkit.kit import get_kit_instances
from _core.driver.parser_lite import ShellHandler
from _core.report.encrypt import check_pub_key_exist
from _core.utils import get_file_absolute_path
from _core.utils import check_result_report
from _core.utils import get_device_log_file
from _core.utils import get_config_value
from _core.utils import exec_cmd
from _core.utils import convert_serial
from _core.utils import convert_mac
from _core.utils import convert_ip
from _core.utils import convert_port
from _core.utils import check_mode
from _core.utils import get_filename_extension
from _core.utils import get_test_component_version
from _core.utils import get_local_ip
from _core.utils import create_dir
from _core.utils import is_proc_running
from _core.utils import check_path_legal
from _core.utils import modify_props
from _core.utils import get_shell_handler
from _core.utils import get_decode
from _core.utils import start_standing_subprocess
from _core.utils import stop_standing_subprocess
from _core.utils import check_mode_in_sys
from _core.utils import get_current_time
from _core.utils import get_cst_time
from _core.utils import get_delta_time_ms
from _core.utils import get_netstat_proc_pid
from _core.utils import calculate_elapsed_time
from _core.utils import copy_folder
from _core.utils import check_uitest_version
from _core.utils import find_file
from _core.utils import get_resource_path
from _core.logger import LogQueue
from _core.environment.manager_env import DeviceSelectionOption
from _core.environment.manager_env import EnvironmentManager
from _core.environment.env_pool import EnvPool
from _core.environment.env_pool import XMLNode
from _core.environment.env_pool import Selector
from _core.environment.env_pool import DeviceNode
from _core.environment.env_pool import DeviceSelector
from _core.environment.env_pool import is_env_pool_run_mode
from _core.environment.device_state import DeviceEvent
from _core.environment.device_state import TestDeviceState
from _core.environment.device_state import DeviceState
from _core.environment.device_state import \
    handle_allocation_event
from _core.environment.device_state import \
    DeviceAllocationState
from _core.environment.device_monitor import DeviceStateListener
from _core.environment.device_monitor import DeviceStateMonitor
from _core.context.life_stage import CaseStart
from _core.context.life_stage import CaseEnd
from _core.context.proxy import Binder
from _core.context.proxy import UploadParams as Scheduler
from _core.context.proxy import SessionInfo
from _core.context.proxy import Connector
from _core.report.suite_reporter import SuiteReporter
from _core.report.suite_reporter import ResultCode
from _core.report.reporter_helper import ExecInfo
from _core.report.reporter_helper import ReportConstant
from _core.report.result_reporter import ResultReporter
from _core.report.reporter_helper import DataHelper
from _core.report.__main__ import main_report
from _core.command.console import Console
from _core.analysis.tracker import TrackEvent, Tracker

VERSION = '6.0.6.210'
__version__ = VERSION

__all__ = [
    "TrackEvent",
    "Tracker",
    "VERSION",
    "Variables",
    "Console",
    "platform_logger",
    "redirect_driver_log_begin",
    "redirect_driver_log_end",
    "get_driver_log_path",
    "Plugin",
    "get_plugin",
    "IDriver",
    "IDevice",
    "IDeviceManager",
    "IProxy",
    "IFilter",
    "IParser",
    "LifeCycle",
    "IShellReceiver",
    "ITestKit",
    "IListener",
    "IReporter",
    "ParamError",
    "DeviceError",
    "LiteDeviceError",
    "ExecuteTerminate",
    "ReportException",
    "HdcError",
    "HdcCommandRejectedException",
    "ShellCommandUnresponsiveException",
    "DeviceUnresponsiveException",
    "AppInstallError",
    "RpcNotRunningError",
    "HapNotSupportTest",
    "DeviceTestType",
    "DeviceLabelType",
    "ManagerType",
    "DeviceOsType",
    "ProductForm",
    "TestType",
    "CKit",
    "ConfigConst",
    "ReportConst",
    "ModeType",
    "TestExecType",
    "ListenerType",
    "GTestConst",
    "CommonParserType",
    "FilePermission",
    "HostDrivenTestType",
    "DeviceConnectorType",
    "DeviceProperties",
    "AdvanceDeviceOption",
    "UserConfigManager",
    "ResourceManager",
    "UniversalReportListener",
    "CaseResult",
    "SuiteResult",
    "SuitesResult",
    "StateRecorder",
    "TestDescription",
    "CollectingTestListener",
    "Task",
    "CaseStart",
    "CaseEnd",
    "Binder",
    "Scheduler",
    "SessionInfo",
    "Connector",
    "SuiteReporter",
    "DeviceSelectionOption",
    "EnvironmentManager",
    "EnvPool",
    "XMLNode",
    "Selector",
    "DeviceNode",
    "DeviceSelector",
    "is_env_pool_run_mode",
    "DeviceEvent",
    "TestDeviceState",
    "DeviceState",
    "handle_allocation_event",
    "DeviceAllocationState",
    "DeviceStateListener",
    "DeviceStateMonitor",
    "JsonParser",
    "junit_para_parse",
    "gtest_para_parse",
    "reset_junit_para",
    "get_app_name_by_tool",
    "get_install_args",
    "remount",
    "disable_keyguard",
    "unlock_screen",
    "unlock_device",
    "get_class",
    "ShellHandler",
    "ResultCode",
    "calculate_elapsed_time",
    "check_pub_key_exist",
    "check_result_report",
    "get_file_absolute_path",
    "get_device_log_file",
    "get_kit_instances",
    "get_config_value",
    "exec_cmd",
    "do_module_kit_setup",
    "do_module_kit_teardown",
    "convert_serial",
    "convert_mac",
    "convert_ip",
    "convert_port",
    "check_mode",
    "get_filename_extension",
    "get_test_component_version",
    "get_local_ip",
    "create_dir",
    "is_proc_running",
    "check_path_legal",
    "modify_props",
    "get_shell_handler",
    "get_decode",
    "start_standing_subprocess",
    "stop_standing_subprocess",
    "check_mode_in_sys",
    "get_current_time",
    "get_delta_time_ms",
    "get_cst_time",
    "get_netstat_proc_pid",
    "check_device_ohca",
    "ExecInfo",
    "ReportConstant",
    "ResultReporter",
    "DataHelper",
    "main_report",
    "Platform",
    "LogQueue",
    "HcpTestMode",
    "LifeStage",
    "AgentMode",
    "copy_folder",
    "check_uitest_version",
    "find_file",
    "get_resource_path",
    "Error",
    "ErrorCategory",
    "Request"
]

def __load_entry_point1(plugin_group, python_version):
    from importlib.metadata import entry_points
    if python_version >= (3, 10, 0):
        for ep in entry_points().select(group=plugin_group):
            ep.load()
        return
    # python3.8、3.9下的实现
    eps = entry_points().get(plugin_group)
    if eps is None:
        return
    for ep in eps:
        ep.load()


def __load_entry_point2(plugin_group):
    import pkg_resources
    for ep in pkg_resources.iter_entry_points(group=plugin_group):
        ep.load()


def __load_external_plugins():
    plugins = [
        Plugin.SCHEDULER, Plugin.DRIVER, Plugin.DEVICE, Plugin.LOG,
        Plugin.PARSER, Plugin.LISTENER, Plugin.TEST_KIT, Plugin.MANAGER,
        Plugin.REPORTER
    ]
    python_version = sys.version_info
    for plugin_group in plugins:
        if python_version >= (3, 8, 0):
            __load_entry_point1(plugin_group, python_version)
        else:
            __load_entry_point2(plugin_group)


__load_external_plugins()
Variables.config = UserConfigManager()
