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

import enum
import platform
from dataclasses import dataclass

__all__ = ["DeviceOsType", "ProductForm", "TestType", "TestExecType",
           "DeviceTestType", "HostTestType", "HostDrivenTestType",
           "SchedulerType", "ListenerType", "ToolCommandType",
           "TEST_DRIVER_SET", "LogMode", "LogType", "CKit",
           "DeviceLabelType", "GTestConst", "ManagerType",
           "ModeType", "ConfigConst", "FilePermission", "CommonParserType",
           "DeviceConnectorType", "ReportConst", "DeviceProperties", "AdvanceDeviceOption",
           "LoggerMethod", "LifeStage", "Platform", "HcpTestMode", "DeviceResult",
           "AgentMode", "CaseResult", "Cluster", "State"]


@dataclass
class DeviceOsType(object):
    """
    DeviceOsType enumeration
    """
    default = "default"
    lite = "lite"


@dataclass
class ProductForm(object):
    """
    ProductForm enumeration
    """
    phone = "phone"
    car = "car"
    television = "tv"
    watch = "watch"
    tablet = 'tablet'
    _2in1 = '2in1'
    wearable = 'wearable'


@dataclass
class TestType(object):
    """
    TestType enumeration
    """
    unittest = "unittest"
    mst = "moduletest"
    systemtest = "systemtest"
    perf = "performance"
    sec = "security"
    reli = "reliability"
    dst = "distributedtest"
    benchmark = "benchmark"
    all = "ALL"


@dataclass
class DeviceLabelType(object):
    """
    DeviceLabelType enumeration
    """
    wifiiot = "wifiiot"
    ipcamera = "ipcamera"
    watch_gt = "watchGT"
    phone = "phone"
    watch = "watch"


TEST_TYPE_DICT = {
    "UT": TestType.unittest,
    "MST": TestType.mst,
    "ST": TestType.systemtest,
    "PERF": TestType.perf,
    "SEC": TestType.sec,
    "RELI": TestType.reli,
    "DST": TestType.dst,
    "ALL": TestType.all,
}


@dataclass
class TestExecType(object):
    """
    TestExecType enumeration according to test execution method
    """
    # A test running on the device
    device_test = "device"
    # A test running on the host (pc)
    host_test = "host"
    # A test running on the host that interacts with one or more devices.
    host_driven_test = "hostdriven"


@dataclass
class DeviceTestType(object):
    """
    DeviceTestType enumeration
    """
    cpp_test = "CppTest"
    dex_test = "DexTest"
    dex_junit_test = "DexJUnitTest"
    hap_test = "HapTest"
    junit_test = "JUnitTest"
    jsunit_test = "JSUnitTest"
    jsunit_test_lite = "JSUnitTestLite"
    ctest_lite = "CTestLite"
    cpp_test_lite = "CppTestLite"
    lite_cpp_test = "LiteUnitTest"
    open_source_test = "OpenSourceTest"
    build_only_test = "BuildOnlyTestLite"
    ltp_posix_test = "LtpPosixTest"
    oh_kernel_test = "OHKernelTest"
    oh_jsunit_test = "OHJSUnitTest"
    hm_os_jsunit_test = "HMOSJSUnitTest"
    hcp_test_lite = "HcpTestLite"
    oh_rust_test = "OHRustTest"
    oh_yara_test = "OHYaraTest"
    hcp_test = "HcpTest"
    ValidatorTest = "ValidatorTest"
    arkuix_jsunit_test = "ARKUIXJSUnitTest"
    oh_jslocal_test = "OHJSLocalTestDriver"
    stability_test = "StabilityTest"
    ux_test = "UXTest"
    global_test = "GlobalTest"
    ark_web_test = "ArkWebTest"
    ark_traverse_test = "ArkTraverseTest"
    ark_perf_test = "ArkWebPerfTest"
    experience_test = "ExperienceTest"


@dataclass
class HostTestType(object):
    """
    HostTestType enumeration
    """
    host_gtest = "HostGTest"
    host_junit_test = "HostJUnitTest"


@dataclass
class HostDrivenTestType(object):
    """
    HostDrivenType enumeration
    """
    device_test = "DeviceTest"
    device_testsuite = "DeviceTestSuite"
    windows_test = "WindowsTest"
    app_test = "AppTest"
    decc_test = "Decc_DeviceTest"


TEST_DRIVER_SET = {
    DeviceTestType.cpp_test,
    DeviceTestType.dex_test,
    DeviceTestType.hap_test,
    DeviceTestType.junit_test,
    DeviceTestType.dex_junit_test,
    DeviceTestType.jsunit_test,
    DeviceTestType.jsunit_test_lite,
    DeviceTestType.cpp_test_lite,
    DeviceTestType.ctest_lite,
    DeviceTestType.lite_cpp_test,
    DeviceTestType.ltp_posix_test,
    DeviceTestType.oh_kernel_test,
    DeviceTestType.oh_jsunit_test,
    HostDrivenTestType.device_test,
    DeviceTestType.ux_test,
    DeviceTestType.stability_test
}


@dataclass
class SchedulerType(object):
    """
    SchedulerType enumeration
    """
    # default scheduler
    scheduler = "Scheduler"
    # module
    module = "module"
    # synchronize
    synchronize = "synchronize"


@dataclass
class LogMode:
    name = "log_mode"
    default = "default"
    no_console = "no_console"


@dataclass
class LogType:
    tool = "Tool"
    device = "Device"


@dataclass
class ListenerType:
    log = "Log"
    report = "Report"
    stack_report = "StackReport"
    upload = "Upload"
    collect = "Collect"
    collect_lite = "CollectLite"
    collect_pass = "CollectPass"


@dataclass
class CommonParserType:
    jsunit = "JSUnit"
    cpptest = "CppTest"
    cpptest_list = "CppTestList"
    junit = "JUnit"
    oh_kernel_test = "OHKernel"
    oh_jsunit = "OHJSUnit"
    oh_jsunit_list = "OHJSUnitList"
    oh_rust = "OHRust"
    oh_yara = "OHYara"
    worker = "Worker"


@dataclass
class ManagerType:
    device = "device"
    lite_device = "device_lite"


@dataclass
class ToolCommandType(object):
    toolcmd_key_help = "help"
    toolcmd_key_show = "show"
    toolcmd_key_run = "run"
    toolcmd_key_quit = "quit"
    toolcmd_key_list = "list"
    toolcmd_key_tool = "tool"


@dataclass
class CKit:
    query = "QueryKit"
    component = "ComponentKit"


@dataclass
class GTestConst(object):
    exec_para_filter = "--gtest_filter"
    exec_para_level = "--gtest_testsize"


@dataclass
class ModeType(object):
    decc = "decc"
    factory = "factory"
    developer = "developer"
    controller = "controller"


@dataclass
class ConfigConst(object):
    action = "action"
    task = "task"
    testlist = "testlist"
    testfile = "testfile"
    testcase = "testcase"
    testdict = "testdict"
    device_sn = "device_sn"
    report_path = "report_path"
    resource_path = "resource_path"
    testcases_path = "testcases_path"
    testargs = "testargs"
    pass_through = "pass_through"
    test_environment = "test_environment"
    exectype = "exectype"
    testtype = "testtype"
    testdriver = "testdriver"
    retry = "retry"
    session = "session"
    dry_run = "dry_run"
    reboot_per_module = "reboot_per_module"
    check_device = "check_device"
    configfile = "config"
    repeat = "repeat"
    subsystems = "subsystems"
    parts = "parts"
    export_report = "export_report"
    renew_report = "renew_report"
    device_info = "device_info"
    kits_in_module = "kits_in_module"
    kits_params = "kits_params"
    auto_retry = "auto_retry"
    enable_unicode = "enable_unicode"
    module_config = "module_config"
    scheduler = "scheduler"
    common_kits = "common_kits"

    # Runtime Constant
    history_report_path = "history_report_path"
    product_info = "product_info"
    task_state = "task_state"
    recover_state = "recover_state"
    need_kit_setup = "need_kit_setup"
    task_kits = "task_kits"
    module_kits = "module_kits"
    common_module_kits = "common_module_kits"
    spt = "spt"
    version = "version"
    component_mapper = "_component_mapper"
    component_base_kit = "component_base_kit"
    support_component = "support_component"

    # Device log
    device_log = "device_log"
    device_log_on = "ON"
    device_log_off = "OFF"
    app_test = "app_test"
    tag_dir = "dir"
    tag_enable = "enable"
    tag_clear = "clear"
    tag_loglevel = "loglevel"
    tag_suite_case_log = "suitecaselog"
    tag_hdc = "hdc"

    # Ignore testcase path
    ignore_testcases_path = "__pycache__|.git|.svn|.idea|.test"

    screenshot_on_failure = "screenshot_on_failure"
    report_plus = "report_plus"
    silence_install = "silence_install"
    env_pool_cache = "env_pool_cache"

    web_resource = "web_resource"
    enable_web_resource = "enable_web_resource"

    tag_url = "url"

    # analysis
    analysis = "analysis"
    before = "before"
    cleanup = "cleanup"
    collapse = "collapse"
    now = "now"
    upload = "upload"
    tag_uploadtrack = "uploadtrack"

    # cluster
    cluster = "cluster"
    service_mode = "service_mode"
    service_port = "service_port"
    control_service_url = "control_service_url"

    class TaskArgs(enum.Enum):
        agent_mode = "agent_mode"
        batch_run_size = "batch_run_size"
        install_user0 = "install_user0"
        kill_uitest = "kill_uitest"
        max_log_line_in_html = "max_log_line_in_html"
        max_driver_threads = "max_driver_threads"
        pass_through = "pass_through"
        repeat = "repeat"
        screenrecorder = "screenrecorder"
        screenshot = "screenshot"
        ui_adaptive = "ui_adaptive"
        web_resource = "web_resource"
        wifi = "wifi"


@dataclass
class ReportConst(object):
    session_id = "session_id"
    command = "command"
    report_path = "report_path"
    unsuccessful_params = "unsuccessful_params"
    data_reports = "data_reports"


class FilePermission(object):
    mode_777 = 0o777
    mode_755 = 0o755
    mode_644 = 0o644


@dataclass
class DeviceConnectorType:
    hdc = "usb-hdc"


@dataclass
class DeviceResult(object):
    """
    DeviceResult enumeration
    """
    code = "code"
    date = "date"
    msg = "msg"
    result = "result"
    data = 'data'


@dataclass
class DeviceProperties(object):
    """
    DeviceProperties enumeration
    """
    system_sdk = "system_sdk"
    system_version = "system_version"
    build_number = "buildNumber"
    cpu_abi = "cpuAbi"
    device_form = "deviceForm"
    software_version = "software_version"
    fault_code = "faultCode"
    fold_screen = "foldScreen"
    hardware = "hardware"
    is_ark = "isArk"
    mac = "mac"
    mobile_service = "mobileService"
    model = "model"
    rom = "rom"
    rooted = "rooted"
    sn = "sn"
    xres = "xres"
    yres = "yres"
    manufacturer = "manufacturer"
    kind = "kind"
    platform = "platform"
    type_ = "type"
    version = "version"
    others = "others"
    alias = "alias"
    reboot_timeout = "reboot_timeout"


@dataclass
class LoggerMethod:
    """
    method name in logger
    """

    info = "info"
    debug = "debug"
    error = "error"
    warning = "warning"
    exception = "exception"


@dataclass
class AdvanceDeviceOption(object):
    """
    method name in logger
    """
    advance = "advance"
    type = "type"
    command = "command"
    product = "product"
    version = "version"
    product_cmd = "product_cmd"
    version_cmd = "version_cmd"
    label = "label"


@dataclass
class Platform(object):
    """
    Platform enumeration
    """
    ohos = "OpenHarmony"


@dataclass
class HcpTestMode(object):
    """
    HcpTestMode enumeration
    """
    hcp_mode = False


@dataclass
class LifeStage(object):
    """
    LifeStage enumeration
    """
    task_start = "TaskStart"
    task_end = "TaskEnd"
    case_start = "CaseStart"
    case_end = "CaseEnd"


@dataclass
class AgentMode(object):
    """
    Agent mode
    """
    hap = "hap"
    abc = "abc"
    bin = "bin"


@dataclass
class CaseResult:
    passed = "Passed"
    failed = "Failed"
    blocked = "Blocked"
    ignored = "Ignored"
    unavailable = "Unavailable"


@dataclass
class UploadType:
    test_type_list = [
        HostDrivenTestType.device_test,
        HostDrivenTestType.windows_test,
        DeviceTestType.stability_test,
        DeviceTestType.ux_test,
        DeviceTestType.ark_web_test,
        DeviceTestType.ark_traverse_test,
        DeviceTestType.ark_perf_test,
        DeviceTestType.global_test,
        DeviceTestType.experience_test
    ]


class Cluster:
    if platform.system() == "Windows":
        local_path = "D:\\Local"
        project_root_path = "D:\\Local\\Projects"
        report_root_path = "D:\\Local\\Reports"
    else:
        local_path = "/data/Local"
        project_root_path = "/data/Local/Projects"
        report_root_path = "/data/Local/Reports"
    service_port = "8000"
    stars = "***"
    controller = "controller"
    worker = "worker"
    worker_logs = "worker_logs"


class State:
    Waiting = "Waiting"
    Running = "Running"
    Completed = "Completed"
    Stopped = "Stopped"
    Stopping = "Stopping"

