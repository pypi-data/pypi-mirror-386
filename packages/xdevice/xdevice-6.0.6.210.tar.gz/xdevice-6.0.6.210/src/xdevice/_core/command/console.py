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

import argparse
import json
import os
import platform
import re
import signal
import sys
import threading
import copy
import time
from collections import namedtuple

from _core.analysis.tracker import Tracker
from _core.config.config_manager import UserConfigManager
from _core.constants import SchedulerType
from _core.constants import ConfigConst
from _core.constants import ReportConst
from _core.constants import ModeType
from _core.constants import ToolCommandType
from _core.environment.manager_env import EnvironmentManager
from _core.error import ErrorMessage
from _core.exception import ParamError
from _core.exception import ExecuteTerminate
from _core.executor.request import Task
from _core.logger import platform_logger
from _core.plugin import Plugin
from _core.plugin import get_plugin
from _core.utils import convert_mac
from _core.utils import SplicingAction
from _core.utils import is_python_satisfied
from _core.report.result_reporter import ResultReporter
from _core.context.center import Context
from _core.context.upload import Uploader
from _core.variables import Variables

__all__ = ["Console"]

LOG = platform_logger("Console")
try:
    if platform.system() != 'Windows':
        import readline
except ImportError:  # pylint:disable=undefined-variable
    LOG.warning("Readline module is not exist.")

MAX_VISIBLE_LENGTH = 49
MAX_RESERVED_LENGTH = 46
Argument = namedtuple('Argument', 'options unparsed valid_param parser')


class Console(object):
    """
    Class representing a console for executing test.
    Main xDevice console providing user with the interface to interact
    """
    __instance = None

    def __new__(cls, *args, **kwargs):
        """
        Singleton instance
        """
        if cls.__instance is None:
            cls.__instance = super(Console, cls).__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        pass

    @classmethod
    def handler_terminate_signal(cls, signalnum, frame):
        # ctrl+c
        del signalnum, frame
        if not Context.is_executing():
            return
        Context.set_execute_status(False)
        LOG.info("Get terminate input")
        if Context.terminate_cmd_exec():
            terminate_thread = threading.Thread(
                target=Context.terminate_cmd_exec())
            terminate_thread.daemon = True
            terminate_thread.start()

    def console(self, args):
        """
        Main xDevice console providing user with the interface to interact
        """
        if not is_python_satisfied():
            sys.exit(0)

        if args is None or len(args) < 2:
            if Variables.config.enable_cluster():
                from _core.cluster.__main__ import cluster_main
                cluster_main()
                time.sleep(1)
            # init environment manager
            Context.set_execute_status(True)
            EnvironmentManager()
            # Enter xDevice console
            self._console()
        else:
            # init environment manager
            Context.set_execute_status(True)
            cmd_args = " ".join(args[1:])
            para_list = self._pre_handle_test_args(cmd_args).split()
            argument = self.argument_parser(para_list)
            options = argument.options
            config_file = options.config
            test_environment = options.test_environment
            if config_file or test_environment:
                EnvironmentManager(environment=test_environment, user_config_file=config_file)
            else:
                EnvironmentManager()
            # Enter xDevice command parser
            self.command_parser(cmd_args)

    def _console(self):
        # Enter xDevice console
        signal.signal(signal.SIGINT, self.handler_terminate_signal)

        while True:
            try:
                usr_input = input(">>> ")
                if usr_input == "":
                    continue

                self.command_parser(usr_input)

            except SystemExit as _:
                LOG.info("Program exit normally!")
                break
            except ExecuteTerminate as _:
                LOG.info("Execution terminated")
            except (IOError, EOFError, KeyboardInterrupt) as error:
                LOG.exception("Input Error: {}".format(error),
                              exc_info=False)

    def argument_parser(self, para_list):
        """
        Argument parser
        """
        options = None
        unparsed = []
        valid_param = True
        parser = None

        try:
            parser = argparse.ArgumentParser(
                description="Specify tests to run.")
            parser.add_argument(
                "action",
                type=str.lower,
                help="Specify action"
            )
            parser.add_argument(
                "task",
                type=str,
                default=None,
                help="Specify task name"
            )
            # 命令参数run acts、run -l xx、run -tc xx互斥
            group1 = parser.add_mutually_exclusive_group()
            group1.add_argument(
                "-l", "--testlist",
                action=SplicingAction,
                type=str,
                nargs='+',
                dest=ConfigConst.testlist,
                default="",
                help="Specify test list"
            )
            group1.add_argument(
                "-tc", "--testcase",
                action="store",
                type=str,
                dest=ConfigConst.testcase,
                default="",
                help="Specify test case"
            )
            group1.add_argument(
                "-tf", "--testfile",
                action=SplicingAction,
                type=str,
                nargs='+',
                dest=ConfigConst.testfile,
                default="",
                help="Specify test list file"
            )
            # 命令参数-c与-env互斥
            group2 = parser.add_mutually_exclusive_group()
            group2.add_argument(
                "-c", "--config",
                action=SplicingAction,
                type=str,
                nargs='+',
                dest=ConfigConst.configfile,
                default="",
                help="Specify config file path"
            )
            group2.add_argument(
                "-env", "--environment",
                action=SplicingAction,
                type=str,
                nargs='+',
                dest=ConfigConst.test_environment,
                default="",
                help="Specify test environment"
            )
            # 命令参数--repeat N、--retry --session xx、--auto_retry [N]互斥
            group3 = parser.add_mutually_exclusive_group()
            group3.add_argument(
                "--repeat",
                type=int,
                default=1,
                dest=ConfigConst.repeat,
                help="number of times that a task is executed repeatedly"
            )
            group3.add_argument(
                "--retry",
                action="store",
                type=str,
                dest=ConfigConst.retry,
                default="",
                help="Specify retry command"
            )
            group3.add_argument(
                "--auto_retry",
                dest=ConfigConst.auto_retry,
                type=int,
                default=0,
                help="- the count of auto retry"
            )

            parser.add_argument(
                "-di", "--device_info",
                dest=ConfigConst.device_info,
                action="store",
                type=str,
                help="- describe device info in json style"
            )
            parser.add_argument("-sn", "--device_sn",
                                action="store",
                                type=str,
                                dest=ConfigConst.device_sn,
                                default="",
                                help="Specify device serial number"
                                )
            parser.add_argument("-rp", "--reportpath",
                                action=SplicingAction,
                                type=str,
                                nargs='+',
                                dest=ConfigConst.report_path,
                                default="",
                                help="Specify test report path"
                                )
            parser.add_argument("-respath", "--resourcepath",
                                action=SplicingAction,
                                type=str,
                                nargs='+',
                                dest=ConfigConst.resource_path,
                                default="",
                                help="Specify test resource path"
                                )
            parser.add_argument("-tcpath", "--testcasespath",
                                action=SplicingAction,
                                type=str,
                                nargs='+',
                                dest=ConfigConst.testcases_path,
                                default="",
                                help="Specify testcases path"
                                )
            parser.add_argument("-ta", "--testargs",
                                action=SplicingAction,
                                type=str,
                                nargs='+',
                                dest=ConfigConst.testargs,
                                default={},
                                help="Specify test arguments"
                                )
            parser.add_argument("-pt", "--passthrough",
                                action="store_true",
                                dest=ConfigConst.pass_through,
                                help="Pass through test arguments"
                                )
            parser.add_argument("-e", "--exectype",
                                action="store",
                                type=str,
                                dest=ConfigConst.exectype,
                                default="device",
                                help="Specify test execute type"
                                )
            parser.add_argument("-t", "--testtype",
                                nargs='*',
                                dest=ConfigConst.testtype,
                                default=[],
                                help="Specify test type" +
                                     "(UT,MST,ST,PERF,SEC,RELI,DST,ALL)"
                                )
            parser.add_argument("-td", "--testdriver",
                                action="store",
                                type=str,
                                dest=ConfigConst.testdriver,
                                default="",
                                help="Specify test driver id"
                                )
            parser.add_argument("-tl", "--testlevel",
                                action="store",
                                type=str,
                                dest="testlevel",
                                default="",
                                help="Specify test level"
                                )
            parser.add_argument("-bv", "--build_variant",
                                action="store",
                                type=str,
                                dest="build_variant",
                                default="release",
                                help="Specify build variant(release,debug)"
                                )
            parser.add_argument("-cov", "--coverage",
                                action="store",
                                type=str,
                                dest="coverage",
                                default="",
                                help="Specify coverage"
                                )
            parser.add_argument("--session",
                                action=SplicingAction,
                                type=str,
                                nargs='+',
                                dest=ConfigConst.session,
                                help="retry task by session id")
            parser.add_argument("--dryrun",
                                action="store_true",
                                dest=ConfigConst.dry_run,
                                help="show retry test case list")
            parser.add_argument("--reboot-per-module",
                                action="store_true",
                                dest=ConfigConst.reboot_per_module,
                                help="reboot devices before executing each "
                                     "module")
            parser.add_argument("--check-device",
                                action="store_true",
                                dest=ConfigConst.check_device,
                                help="check the test device meets the "
                                     "requirements")
            parser.add_argument("-le", "--local_execution_log_path",
                                dest="local_execution_log_path",
                                help="- The local execution log path.")
            parser.add_argument("-s", "--subsystem",
                                dest="subsystems",
                                action="store",
                                type=str,
                                help="- Specify the list of subsystem")
            parser.add_argument("-p", "--part",
                                dest="parts",
                                action="store",
                                type=str,
                                help="- Specify the list of part")
            parser.add_argument("-kim", "--kits_in_module",
                                dest=ConfigConst.kits_in_module,
                                action=SplicingAction,
                                type=str,
                                nargs='+',
                                default="",
                                help="- kits that are used for specify module")
            parser.add_argument("--kp", "--kits_params",
                                dest=ConfigConst.kits_params,
                                action=SplicingAction,
                                type=str,
                                nargs='+',
                                default="",
                                help='- the params of kits that related to'
                                     ' module'
                                )
            parser.add_argument("--enable_unicode",
                                dest=ConfigConst.enable_unicode,
                                action="store_true",
                                help="enable unicode about test args."
                                     "It must be used with and immediately "
                                     "following the -ta or --testargs parameter")
            parser.add_argument("-module_config",
                                action=SplicingAction,
                                type=str,
                                nargs='+',
                                dest=ConfigConst.module_config,
                                default="",
                                help="Specify module config json path"),
            parser.add_argument("--scheduler",
                                dest=ConfigConst.scheduler,
                                action="store",
                                type=str,
                                default="default",
                                help="Select different scheduling schemes."
                                     "--scheduler module")

            self._params_pre_processing(para_list)
            (options, unparsed) = parser.parse_known_args(para_list)
            if unparsed:
                LOG.warning("Unparsed input: %s", " ".join(unparsed))
            self._params_post_processing(options)
        except SystemExit as _:
            valid_param = False
            parser.print_help()
            LOG.warning("Parameter parsing system exit exception.")
        return Argument(options, unparsed, valid_param, parser)

    @classmethod
    def _params_pre_processing(cls, para_list):
        para_list_len = len(para_list)
        if para_list_len <= 1:
            para_list.insert(1, Task.EMPTY_TASK)
        elif para_list_len > 1:
            item1 = str(para_list[1])
            # cluster的任务id是由日期加时间组成的（如2025-04-12-15-28-10-944103）
            # 当使用指令“list 任务id”查询任务时，不用加Task.EMPTY_TASK
            if "-" in item1 and not re.match(r'\d{4}-(?:\d{2}-){5}\d{6}', item1):
                para_list.insert(1, Task.EMPTY_TASK)
        for index, param in enumerate(para_list):
            if param == "--retry":
                if index + 1 == len(para_list):
                    para_list.append("retry_previous_command")
                elif "-" in str(para_list[index + 1]):
                    para_list.insert(index + 1, "retry_previous_command")
            elif param == "-->":
                para_list[index] = "!%s" % param

    def _params_post_processing(self, options):
        # 重新初始化对象，无需重新进入命令交互窗口，可以使用最新的配置信息
        Variables.config = UserConfigManager()
        if options.config:
            Variables.config = UserConfigManager(config_file=options.config)
            Tracker.update_analysis_config()
        if options.test_environment:
            Variables.config = UserConfigManager(env=options.test_environment)
            Tracker.update_analysis_config()
        self._update_task_args(options)

        # params post-processing
        if options.task == Task.EMPTY_TASK:
            setattr(options, ConfigConst.task, "")
        if options.testargs:
            if options.enable_unicode:
                test_args = str(options.testargs).encode("utf-8").decode('unicode_escape')
                setattr(options, ConfigConst.testargs, test_args)
            if not options.pass_through:
                test_args = self._parse_combination_param(options.testargs)
                setattr(options, ConfigConst.testargs, test_args)
            else:
                setattr(options, ConfigConst.testargs, {
                    ConfigConst.pass_through: options.testargs})
        if not options.resource_path:
            setattr(options, ConfigConst.resource_path, Variables.config.get_resource_path())
        if not options.testcases_path:
            setattr(options, ConfigConst.testcases_path, Variables.config.get_testcases_dir())
        setattr(options, ConfigConst.device_log, Variables.config.devicelog)
        if options.subsystems:
            subsystem_list = str(options.subsystems).split(";")
            setattr(options, ConfigConst.subsystems, subsystem_list)
        if options.parts:
            part_list = str(options.parts).split(";")
            setattr(options, ConfigConst.parts, part_list)
        if options.device_info:
            device_info = self._parse_extension_device_info(str(options.device_info))
            setattr(options, ConfigConst.device_info, device_info)
        if options.kits_in_module:
            kit_list = str(options.kits_in_module).split(";")
            setattr(options, ConfigConst.kits_in_module, kit_list)
            params = getattr(options, ConfigConst.kits_params, "")
            setattr(options, ConfigConst.kits_params,
                    self._parse_kit_params(params))

    def command_parser(self, args):
        try:
            Context.command_queue().append(args)
            LOG.info("Input command: {}".format(convert_mac(args)))
            args = self._pre_handle_test_args(args)
            para_list = args.split()
            argument = self.argument_parser(para_list)
            options = argument.options
            if options is None or not argument.valid_param:
                LOG.warning("Options is None.")
                return
            if options.action == ToolCommandType.toolcmd_key_run and \
                    options.retry:
                if hasattr(options, ConfigConst.auto_retry):
                    setattr(options, ConfigConst.auto_retry, 0)
                options = self._get_retry_options(options, argument.parser)
                if options.dry_run:
                    history_report_path = getattr(options,
                                                  "history_report_path", "")
                    self._list_retry_case(history_report_path)
                    return
            else:
                from xdevice import SuiteReporter
                SuiteReporter.clear_failed_case_list()
                SuiteReporter.clear_report_result()

            command = options.action
            if command == "":
                LOG.info("Command is empty.")
                return

            self._process_command(command, options, para_list, argument.parser)
        except (ParamError, ValueError, TypeError, SyntaxError,
                AttributeError) as exception:
            LOG.exception(exception, exc_info=False)
            Uploader.upload_unavailable_result(str(exception.args))
            Uploader.upload_report_end()
        finally:
            if isinstance(Context.command_queue().get(-1), str):
                Context.command_queue().pop()

    def _process_command(self, command, options, para_list, parser):
        if command.startswith(ToolCommandType.toolcmd_key_help):
            self._process_command_help(parser, para_list)
        elif command.startswith(ToolCommandType.toolcmd_key_show):
            self._process_command_show(para_list)
        elif command.startswith(ToolCommandType.toolcmd_key_run):
            self._process_command_run(command, options)
        elif command.startswith(ToolCommandType.toolcmd_key_quit):
            self._process_command_quit(command)
        elif command.startswith(ToolCommandType.toolcmd_key_list):
            self._process_command_list(command, para_list)
        elif command.startswith(ToolCommandType.toolcmd_key_tool):
            self._process_command_tool(command, para_list, options)
        else:
            LOG.error("Unsupported command action", error_no="00100",
                      action=command)

    def _get_retry_options(self, options, parser):
        input_options = copy.deepcopy(options)
        # get history command, history report path
        history_command, history_report_path = self._parse_retry_option(
            options)
        LOG.info("History command: %s", history_command)
        if not os.path.exists(history_report_path) and \
                Context.session().mode != ModeType.decc:
            raise ParamError(ErrorMessage.Common.Code_0101005.format(history_report_path))

        # parse history command, set history report path
        is_dry_run = True if options.dry_run else False

        history_command = self._wash_history_command(history_command)
        history_command_inner = self._pre_handle_test_args(history_command)

        argument = self.argument_parser(history_command_inner.split())
        argument.options.dry_run = is_dry_run
        setattr(argument.options, "history_report_path", history_report_path)
        # modify history_command -rp param and -sn param
        for option_tuple in self._get_to_be_replaced_option(parser):
            history_command = self._replace_history_option(
                history_command, (input_options, argument.options),
                option_tuple)

        # add history command to command_queue
        LOG.info("Retry command: %s", history_command)
        Context.command_queue().update(-1, history_command)
        return argument.options

    @classmethod
    def _process_command_help(cls, parser, para_list):
        if para_list[0] == ToolCommandType.toolcmd_key_help:
            if len(para_list) == 2:
                cls.display_help_command_info(para_list[1])
            else:
                parser.print_help()
        else:
            LOG.error("Wrong help command. Use 'help' to print help")
        return

    @classmethod
    def _process_command_show(cls, para_list):
        if para_list[0] == ToolCommandType.toolcmd_key_show:
            pass
        else:
            LOG.error("Wrong show command.")
        return

    @classmethod
    def _process_command_run(cls, command, options):
        test_file = options.testfile.strip()
        if test_file and Variables.config.enable_cluster():
            from _core.cluster.utils import console_create_task
            if console_create_task(test_file):
                return

        scheduler = get_plugin(plugin_type=Plugin.SCHEDULER,
                               plugin_id=SchedulerType.scheduler)[0]
        if scheduler is None:
            LOG.error("Can not find the scheduler plugin.")
        else:
            scheduler.exec_command(command, options)

    def _process_command_list(self, command, para_list):
        if command != ToolCommandType.toolcmd_key_list:
            LOG.error("Wrong list command.")
            return
        if Variables.config.enable_cluster():
            self._cluster_list(para_list)
            return
        if len(para_list) > 1:
            if para_list[1] == "history":
                self._list_history()
            elif para_list[1] == "devices" or para_list[1] == Task.EMPTY_TASK:
                EnvironmentManager().list_devices()
            else:
                self._list_task_id(para_list[1])
            return
        # list devices
        EnvironmentManager().list_devices()

    @staticmethod
    def _cluster_list(para_list):
        from _core.cluster.utils import console_list_devices
        from _core.cluster.utils import console_list_task
        if len(para_list) > 1:
            item = para_list[1]
            if item == "history":
                console_list_task()
            elif item == "devices" or item == Task.EMPTY_TASK:
                console_list_devices()
            else:
                console_list_task(task_id=item)
            return
        console_list_devices()

    @classmethod
    def _process_command_quit(cls, command):
        if command == ToolCommandType.toolcmd_key_quit:
            env_manager = EnvironmentManager()
            env_manager.env_stop()
            sys.exit(0)
        else:
            LOG.error("Wrong exit command. Use 'quit' to quit program")
        return

    @classmethod
    def _process_command_tool(cls, command, para_list, options):
        if not command.startswith(ToolCommandType.toolcmd_key_tool):
            LOG.error("Wrong tool command.")
            return
        if len(para_list) > 2:
            tool_name = para_list[1]
            if tool_name in [ConfigConst.renew_report, ConfigConst.export_report]:
                report_path = str(getattr(options, ConfigConst.report_path, ""))
                if not report_path:
                    LOG.error("report path must be specified, you can pass it with option -rp")
                    return
                cls._report_helper(report_path.split(";"), tool_name)

    @staticmethod
    def _parse_combination_param(combination_value):
        # sample: size:xxx1;exclude-annotation:xxx
        parse_result = {}
        key_value_pairs = str(combination_value).split(";")
        for key_value_pair in key_value_pairs:
            key, value = key_value_pair.split(":", 1)
            if not value:
                raise ParamError(ErrorMessage.Common.Code_0101006.format(value))
            if ConfigConst.pass_through not in key:
                value_list = str(value).split(",")
                exist_list = parse_result.get(key, [])
                exist_list.extend(value_list)
                parse_result[key] = exist_list
            else:
                parse_result[key] = value
        return parse_result

    @staticmethod
    def _parse_extension_device_info(device_info_str):
        parse_result = json.loads(device_info_str).get("devices", None)
        if isinstance(parse_result, list):
            parse_result = [x for x in parse_result if 'sn' in x and 'type' in x]
        else:
            parse_result = None
        return parse_result

    @staticmethod
    def _update_task_args(options):
        args = {}
        repeat = options.repeat
        # 命令行repeat设值大于1时，才更新
        if repeat > 1:
            args.update({ConfigConst.repeat: repeat})
        if options.testargs and not options.pass_through:
            for combine_value in options.testargs.split(";"):
                arg = combine_value.split(":", 1)
                args.update({arg[0].strip(): arg[1].strip()})
        Variables.config.update_task_args(new_args=args)

    @classmethod
    def _list_history(cls):
        print("Command history:")
        print("{0:<16}{1:<50}{2:<50}".format(
            "TaskId", "Command", "ReportPath"))
        for command_info in Context.command_queue().list_history():
            command, report_path = command_info[1], command_info[2]
            if len(command) > MAX_VISIBLE_LENGTH:
                command = "%s..." % command[:MAX_RESERVED_LENGTH]
            if len(report_path) > MAX_VISIBLE_LENGTH:
                report_path = "%s..." % report_path[:MAX_RESERVED_LENGTH]
            print("{0:<16}{1:<50}{2:<50}".format(
                command_info[0], command, report_path))

    @classmethod
    def _list_task_id(cls, task_id):
        print("List task:")
        task_id, command, report_path = task_id, "", ""
        for command_info in Context.command_queue().list_history():
            if command_info[0] != task_id:
                continue
            task_id, command, report_path = command_info
            break
        print("{0:<16}{1:<100}".format("TaskId:", task_id))
        print("{0:<16}{1:<100}".format("Command:", command))
        print("{0:<16}{1:<100}".format("ReportPath:", report_path))

    @classmethod
    def _list_retry_case(cls, history_path):
        params = ResultReporter.get_task_info_params(history_path)
        if not params:
            raise ParamError(ErrorMessage.Common.Code_0101007)
        session_id, command, report_path, failed_list = \
            params[ReportConst.session_id], params[ReportConst.command], \
                params[ReportConst.report_path], \
                [(module, failed) for module, case_list in params[ReportConst.unsuccessful_params].items()
                 for failed in case_list]
        if Context.session().mode == ModeType.decc:
            from xdevice import SuiteReporter
            SuiteReporter.failed_case_list = failed_list
            return

        # draw tables in console
        left, middle, right = 23, 49, 49
        two_segments = "{0:-<%s}{1:-<%s}+" % (left, middle + right)
        two_rows = "|{0:^%s}|{1:^%s}|" % (left - 1, middle + right - 1)

        three_segments = "{0:-<%s}{1:-<%s}{2:-<%s}+" % (left, middle, right)
        three_rows = "|{0:^%s}|{1:^%s}|{2:^%s}|" % \
                     (left - 1, middle - 1, right - 1)
        if len(session_id) > middle + right - 1:
            session_id = "%s..." % session_id[:middle + right - 4]
        if len(command) > middle + right - 1:
            command = "%s..." % command[:middle + right - 4]
        if len(report_path) > middle + right - 1:
            report_path = "%s..." % report_path[:middle + right - 4]

        print(two_segments.format("+", '+'))
        print(two_rows.format("SessionId", session_id))
        print(two_rows.format("Command", command))
        print(two_rows.format("ReportPath", report_path))

        print(three_segments.format("+", '+', '+'))
        print(three_rows.format("Module", "Testsuite", "Testcase"))
        print(three_segments.format("+", '+', '+'))
        for module, failed in failed_list:
            # all module is failed
            if "#" not in failed:
                class_name = "-"
                test = "-"
            # others, get failed cases info
            else:
                pos = failed.rfind("#")
                class_name = failed[:pos]
                test = failed[pos + 1:]
            if len(module) > left - 1:
                module = "%s..." % module[:left - 4]
            if len(class_name) > middle - 1:
                class_name = "%s..." % class_name[:middle - 4]
            if len(test) > right - 1:
                test = "%s..." % test[:right - 4]
            print(three_rows.format(module, class_name, test))
        print(three_segments.format("+", '+', '+'))

    @classmethod
    def _find_history_path(cls, session):
        if os.path.isdir(session):
            return session

        target_path = os.path.join(
            Variables.exec_dir, Variables.report_vars.report_dir, session)
        if not os.path.isdir(target_path):
            raise ParamError(ErrorMessage.Common.Code_0101008.format(session))

        return target_path

    def _parse_retry_option(self, options):
        if Context.session().mode == ModeType.decc:
            if Context.command_queue().size() < 2:
                raise ParamError(ErrorMessage.Common.Code_0101009)
            _, history_command, history_report_path = \
                Context.command_queue().get(-2)
            return history_command, history_report_path

        # get history_command, history_report_path
        if options.retry == "retry_previous_command":
            history_path = os.path.join(Variables.temp_dir, "latest")
            if options.session:
                history_path = self._find_history_path(options.session)

            params = ResultReporter.get_task_info_params(history_path)
            if not params:
                error_msg = ErrorMessage.Common.Code_0101009 if not options.session \
                    else ErrorMessage.Common.Code_0101010.format(options.session)

                raise ParamError(error_msg)
            history_command, history_report_path = params[ReportConst.command], params[ReportConst.report_path]
        else:
            history_command, history_report_path = "", ""
            for command_tuple in Context.command_queue().list_history():
                if command_tuple[0] != options.retry:
                    continue
                history_command, history_report_path = \
                    command_tuple[1], command_tuple[2]
                break
            if not history_command:
                raise ParamError(ErrorMessage.Common.Code_0101011.format(options.retry))
        return history_command, history_report_path

    @classmethod
    def display_help_command_info(cls, command):
        if command == ToolCommandType.toolcmd_key_run:
            print(RUN_INFORMATION)
        elif command == ToolCommandType.toolcmd_key_list:
            print(LIST_INFORMATION)
        elif command == "empty":
            print(GUIDE_INFORMATION)
        else:
            print("'%s' command no help information." % command)

    @classmethod
    def _replace_history_option(cls, history_command, options_tuple,
                                target_option_tuple):
        input_options, history_options = options_tuple
        option_name, short_option_str, full_option_str = target_option_tuple
        history_value = getattr(history_options, option_name, "")
        input_value = getattr(input_options, option_name, "")
        if history_value:
            if input_value:
                history_command = history_command.replace(history_value,
                                                          input_value)
                setattr(history_options, option_name, input_value)
            else:
                history_command = str(history_command).replace(
                    history_value, "").replace(full_option_str, ""). \
                    replace(short_option_str, "")
        else:
            if input_value:
                history_command = "{}{}".format(
                    history_command, " %s %s" % (short_option_str,
                                                 input_value))
                setattr(history_options, option_name, input_value)

        return history_command.strip()

    @classmethod
    def _get_to_be_replaced_option(cls, parser):
        name_list = ["report_path", "device_sn"]
        option_str_list = list()
        action_list = getattr(parser, "_actions", [])
        if action_list:
            for action in action_list:
                if action.dest not in name_list:
                    continue
                option_str_list.append((action.dest, action.option_strings[0],
                                        action.option_strings[1]))
        else:
            option_str_list = [("report_path", "-rp", "--reportpath"),
                               ("device_sn", "-sn", "--device_sn")]
        return option_str_list

    @classmethod
    def _report_helper(cls, report_list, tool_name):
        from _core.report.__main__ import main_report, export_report
        for report in report_list:
            run_command = Context.command_queue().pop()
            Context.command_queue().append(("", run_command, report))
            sys.argv.insert(1, report)
            if tool_name == ConfigConst.renew_report:
                main_report()
            elif tool_name == ConfigConst.export_report:
                export_report()
            sys.argv.pop(1)

    @classmethod
    def _parse_kit_params(cls, kits_params):
        params_result = dict()
        if not kits_params:
            return params_result
        kits_params_list = str(kits_params).split(" ")
        if len(kits_params_list) % 2 != 0:
            LOG.warning("Unavailable kit params")
        else:
            for index in range(0, len(kits_params_list), 2):
                params_result.update(
                    {kits_params_list[index]: kits_params_list[index + 1]})
        return params_result

    @classmethod
    def _wash_history_command(cls, history_command):
        # clear redundant content in history command. e.g. repeat,sn
        if "--repeat" in history_command or "-sn" in history_command \
                or "--auto_retry" in history_command:
            split_list = list(history_command.split())
            if "--repeat" in split_list:
                pos = split_list.index("--repeat")
                split_list = split_list[:pos] + split_list[pos + 2:]
            if "-sn" in split_list:
                pos = split_list.index("-sn")
                split_list = split_list[:pos] + split_list[pos + 2:]
            if "--auto_retry" in split_list:
                pos = split_list.index("--auto_retry")
                split_list = split_list[:pos] + split_list[pos + 2:]
            return " ".join(split_list)
        else:
            return history_command

    @classmethod
    def _pre_handle_test_args(cls, args):
        res = re.match(".+(?:-ta|--testargs)\\s+(.+)\\s+--enable_unicode",
                       args, re.S)
        if not res:
            return args
        unicode = ''.join(rf'\u{ord(x):04x}' for x in res.group(1))
        args = args[:res.start(1)] + unicode + args[res.end(1):]
        return args


RUN_INFORMATION = """run:
    This command is used to execute the selected testcases.
    It includes a series of processes such as use case compilation, \
execution, and result collection.

usage: run [-l TESTLIST [TESTLIST ...] | -tf TESTFILE
           [TESTFILE ...]] [-tc TESTCASE] [-c CONFIG] [-sn DEVICE_SN]
           [-rp REPORT_PATH [REPORT_PATH ...]]
           [-respath RESOURCE_PATH [RESOURCE_PATH ...]]
           [-tcpath TESTCASES_PATH [TESTCASES_PATH ...]]
           [-ta TESTARGS [TESTARGS ...]] [-pt]
           [-env TEST_ENVIRONMENT [TEST_ENVIRONMENT ...]]
           [-e EXECTYPE] [-t [TESTTYPE [TESTTYPE ...]]]
           [-td TESTDRIVER] [-tl TESTLEVEL] [-bv BUILD_VARIANT]
           [-cov COVERAGE] [--retry RETRY] [--session SESSION]
           [--dryrun] [--reboot-per-module] [--check-device]
           [--repeat REPEAT] [--scheduler SCHEDULER]
           action task

Specify tests to run.

positional arguments:
  action                Specify action
  task                  Specify task name,such as "ssts", "acts", "hits"

optional arguments:
    -h, --help            show this help message and exit
    -l TESTLIST [TESTLIST ...], --testlist TESTLIST [TESTLIST ...]
                        Specify test list
    -tf TESTFILE [TESTFILE ...], --testfile TESTFILE [TESTFILE ...]
                        Specify test list file
    -tc TESTCASE, --testcase TESTCASE
                        Specify test case
    -c CONFIG, --config CONFIG
                        Specify config file path
    -sn DEVICE_SN, --device_sn DEVICE_SN
                        Specify device serial number
    -rp REPORT_PATH [REPORT_PATH ...], --reportpath REPORT_PATH [REPORT_PATH \
...]
                        Specify test report path
    -respath RESOURCE_PATH [RESOURCE_PATH ...], --resourcepath RESOURCE_PATH \
[RESOURCE_PATH ...]
                        Specify test resource path
    -tcpath TESTCASES_PATH [TESTCASES_PATH ...], --testcasespath \
TESTCASES_PATH [TESTCASES_PATH ...]
                        Specify testcases path
    -ta TESTARGS [TESTARGS ...], --testargs TESTARGS [TESTARGS ...]
                        Specify test arguments
    -pt, --passthrough    Pass through test arguments
    -env TEST_ENVIRONMENT [TEST_ENVIRONMENT ...], --environment \
TEST_ENVIRONMENT [TEST_ENVIRONMENT ...]
                        Specify test environment
    -e EXECTYPE, --exectype EXECTYPE
                        Specify test execute type
    -t [TESTTYPE [TESTTYPE ...]], --testtype [TESTTYPE [TESTTYPE ...]]
                        Specify test type(UT,MST,ST,PERF,SEC,RELI,DST,ALL)
    -td TESTDRIVER, --testdriver TESTDRIVER
                        Specify test driver id
    -tl TESTLEVEL, --testlevel TESTLEVEL
                        Specify test level
    -bv BUILD_VARIANT, --build_variant BUILD_VARIANT
                        Specify build variant(release,debug)
    -cov COVERAGE, --coverage COVERAGE
                        Specify coverage
    --retry RETRY          Specify retry command
    --session SESSION      retry task by session id
    --dryrun               show retry test case list
    --reboot-per-module    reboot devices before executing each module
    --check-device         check the test device meets the requirements
    --repeat REPEAT        number of times that a task is executed repeatedly
    --scheduler SCHEDULER  Select different scheduling schemes

Examples:
    run -l <module name>;<module name>
    run -tf test/resource/<test file name>.txt 
    
    run –l <module name> -sn <device serial number>;<device serial number>
    run –l <module name> -respath <path of resource>
    run –l <module name> -ta size:large
    run –l <module name> –ta class:<package>#<class>#<method>
    run –l <module name> -ta size:large -pt
    run –l <module name> –env <the content string of user_config.xml>
    run –l <module name> –e device 
    run –l <module name> –t ALL
    run –l <module name> –td CppTest
    run –l <module name> -tcpath resource/testcases
    
    run ssts
    run ssts –tc <python script name>;<python script name>
    run ssts -sn <device serial number>;<device serial number>
    run ssts -respath <path of resource>
    ... ...   
    
    run acts
    run acts –tc <python script name>;<python script name>
    run acts -sn <device serial number>;<device serial number>
    run acts -respath <path of resource>
    ... ...
    
    run hits
    ... ...
    
    run --retry
    run --retry --session <report folder name>
    run --retry --dryrun
"""

LIST_INFORMATION = "list:" + """
    This command is used to display device list and task record.\n
usage: 
    list 
    list history
    list <id>
       
Introduction:
    list:         display device list 
    list history: display history record of a serial of tasks
    list <id>:    display history record about task what contains specific id

Examples:
    list
    list history
    list 6e****90
"""

GUIDE_INFORMATION = """help:
    use help to get  information.
    
usage:
    run:  Display a list of supported run command.
    list: Display a list of supported device and task record.

Examples:
    help run 
    help list
"""
