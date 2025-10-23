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

import json
import os
import time
from enum import Enum
from threading import RLock

from _core.constants import CaseResult
from _core.constants import ModeType
from _core.logger import platform_logger
from _core.report.encrypt import check_pub_key_exist
from _core.report.reporter_helper import Case
from _core.report.reporter_helper import DataHelper
from _core.report.reporter_helper import ReportConstant
from _core.context.center import Context

LOG = platform_logger("SuiteReporter")
SUITE_REPORTER_LOCK = RLock()


class ResultCode(Enum):
    UNKNOWN = -1010
    BLOCKED = -1
    PASSED = 0
    FAILED = 1
    SKIPPED = 2
    UNAVAILABLE = 3


class SuiteReporter:
    suite_list = []
    suite_report_result = []
    failed_case_list = []
    history_report_result = []

    def __init__(self, results, report_name, report_path=None, **kwargs):
        """
        Create suite report
        :param results: [(suite_result, [case_results]),
                        (suite_result, [case_results]), ...]
        :param report_name: suite report name
        :param report_path: suite report path
        """
        self.results = results
        self.data_helper = DataHelper()
        self.report_name = report_name
        self.report_path = report_path
        repeat = kwargs.get("repeat", 1)
        repeat_round = kwargs.get("repeat_round", 1)
        round_folder = f"round{repeat_round}" if repeat > 1 else ""
        dir_path = os.path.join(self.report_path, round_folder)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        self.suite_data_path = os.path.join(dir_path, "{}{}".format(report_name, self.data_helper.DATA_REPORT_SUFFIX))
        self.kwargs = kwargs
        if not check_pub_key_exist() and Context.session().mode != ModeType.decc:
            SuiteReporter.suite_report_result.clear()

    def create_empty_report(self):
        # create empty data report only for single suite
        if len(self.results) != 1:
            LOG.error("Can only create one empty data report once")
            return
        suite_result, _ = self.results[0]

        # initial test suites element
        test_suites_element, test_suites_attributes, _ = \
            self._initial_test_suites()
        if self.kwargs.get(ReportConstant.result_kind) == CaseResult.unavailable:
            test_suites_attributes[ReportConstant.unavailable] = 1
        else:
            test_suites_attributes[ReportConstant.disabled] = 1
        self.data_helper.set_element_attributes(test_suites_element,
                                                test_suites_attributes)

        # initial test suite element
        test_suite_element, test_suite_attributes = self._initial_test_suite(
            suite_result)
        test_suite_element.text, test_suite_element.tail = \
            "", self.data_helper.LINE_BREAK
        if self.kwargs.get(ReportConstant.result_kind) == CaseResult.unavailable:
            test_suite_attributes[ReportConstant.unavailable] = 1
        else:
            test_suite_attributes[ReportConstant.disabled] = 1
        test_suite_attributes[ReportConstant.message] = suite_result.stacktrace

        if Context.session().mode == ModeType.decc:
            test_suite_attributes[ReportConstant.result] = ReportConstant.false
        self.data_helper.set_element_attributes(test_suite_element,
                                                test_suite_attributes)

        # append test suite element
        test_suites_element.append(test_suite_element)

        # generate report
        if test_suites_element:
            if Context.session().mode != ModeType.decc:
                self.data_helper.generate_report(test_suites_element,
                                                 self.suite_data_path)
            SuiteReporter.append_report_result((
                self.suite_data_path, self.data_helper.to_string(
                    test_suites_element)))

    def generate_data_report(self):
        # construct test suites element
        test_suites_element = self._construct_test_suites()

        # generate report
        if test_suites_element:
            self.data_helper.generate_report(test_suites_element,
                                             self.suite_data_path)
            SuiteReporter.append_report_result((
                self.suite_data_path, self.data_helper.to_string(
                    test_suites_element)))

    def _construct_test_suites(self):
        # initial test suites element
        test_suites_element, test_suites_attributes, need_update_attributes = \
            self._initial_test_suites()

        # construct test suite element
        for suite_result, case_results in self.results:
            test_suite_element, test_suite_attributes = \
                self._construct_test_suite(suite_result, case_results)

            # add test suite element
            test_suites_element.append(test_suite_element)

            # update and set test suites element attributes
            for need_update_attribute in need_update_attributes:
                test_suites_attributes[need_update_attribute] += \
                    test_suite_attributes.get(need_update_attribute, 0)
        test_suites_attributes[ReportConstant.time] = \
            round(test_suites_attributes.get(ReportConstant.time), 3)

        if test_suites_element:
            test_suite_element = test_suites_element[-1]
            test_suite_element.tail = self.data_helper.LINE_BREAK
        else:
            LOG.error("%s no suite result exists" % self.report_name)

        # set test suites element attributes
        self.data_helper.set_element_attributes(test_suites_element,
                                                test_suites_attributes)
        return test_suites_element

    def _initial_test_suites(self):
        test_suites_element = self.data_helper.initial_suites_element()
        test_suites_attributes = {
            ReportConstant.name: self.report_name,
            ReportConstant.time_stamp: time.strftime(ReportConstant.time_format, time.localtime()),
            ReportConstant.time: 0,
            ReportConstant.errors: 0,
            ReportConstant.disabled: 0,
            ReportConstant.failures: 0,
            ReportConstant.tests: 0,
            ReportConstant.ignored: 0,
            ReportConstant.unavailable: 0,
            # module's failure message
            ReportConstant.message: self.kwargs.get(ReportConstant.message, "")
        }
        module_name = self.kwargs.get(ReportConstant.module_name, "")
        if module_name:
            test_suites_attributes[ReportConstant.name] = module_name
        need_update_attributes = [
            ReportConstant.time,
            ReportConstant.errors,
            ReportConstant.tests,
            ReportConstant.ignored,
            ReportConstant.disabled,
            ReportConstant.failures,
            ReportConstant.unavailable
        ]
        return test_suites_element, test_suites_attributes, need_update_attributes

    def _construct_test_suite(self, suite_result, case_results):
        # initial test suite element
        test_suite_element, test_suite_attributes = self._initial_test_suite(
            suite_result)

        # get test case elements that are children of test suite element
        test_case_elements = []
        for case_result in case_results:
            # initial test case element
            test_case_element, test_case_attributes = self._initial_test_case(case_result)

            # update attributes according to case result
            self.update_attributes(case_result, test_case_attributes, test_suite_attributes)

            # set test case attributes and add to test_suite_element
            self.data_helper.set_element_attributes(test_case_element, test_case_attributes)

            tests_result = getattr(case_result, "tests_result", None)
            if not isinstance(tests_result, list):
                tests_result = []
            for index, test in enumerate(tests_result):
                if index == 0:
                    test_case_element.text = self.data_helper.LINE_BREAK + self.data_helper.INDENT * 3
                # create test element and set element
                test_element, test_attributes = self._initial_test_element(test)
                if index == len(tests_result) - 1:
                    test_element.tail = self.data_helper.LINE_BREAK + self.data_helper.INDENT * 2
                self.data_helper.set_element_attributes(test_element, test_attributes)
                test_case_element.append(test_element)

            test_case_elements.append(test_case_element)
        test_suite_attributes[ReportConstant.disabled] += max(int(
            test_suite_attributes.get(ReportConstant.tests) -
            len(test_case_elements)), 0)
        if test_case_elements:
            child = test_case_elements[-1]
            child.tail = self.data_helper.LINE_BREAK_INDENT
        else:
            LOG.debug("No case executed")
        test_suite_element.extend(test_case_elements)

        # set test suite attributes
        self.data_helper.set_element_attributes(test_suite_element,
                                                test_suite_attributes)
        return test_suite_element, test_suite_attributes

    @classmethod
    def update_attributes(cls, case_result, test_case_attributes,
                          test_suite_attributes):
        if case_result.code == ResultCode.PASSED.value:
            test_case_attributes[ReportConstant.status] = ReportConstant.run
            test_case_attributes[ReportConstant.result] = ReportConstant.true
            test_case_attributes[ReportConstant.message] = ""
        elif case_result.code == ResultCode.FAILED.value:
            test_case_attributes[ReportConstant.status] = ReportConstant.run
            test_case_attributes[ReportConstant.result] = ReportConstant.false
            test_suite_attributes[ReportConstant.failures] = \
                test_suite_attributes[ReportConstant.failures] + 1
        elif case_result.code == ResultCode.SKIPPED.value:
            test_case_attributes[ReportConstant.status] = ReportConstant.skip
            test_case_attributes[ReportConstant.result] = ReportConstant.false
            test_suite_attributes[ReportConstant.ignored] = \
                test_suite_attributes[ReportConstant.ignored] + 1
        elif case_result.code == ResultCode.UNAVAILABLE.value:
            test_case_attributes[ReportConstant.status] = ReportConstant.unavailable
            test_case_attributes[ReportConstant.result] = ReportConstant.false
            key = ReportConstant.unavailable
            test_suite_attributes.update({key: test_suite_attributes.get(key, 0) + 1})
        else:  # ResultCode.UNKNOWN.value or other value
            test_case_attributes[ReportConstant.status] = \
                ReportConstant.disable
            test_case_attributes[ReportConstant.result] = ReportConstant.false
            test_suite_attributes[ReportConstant.disabled] = \
                test_suite_attributes[ReportConstant.disabled] + 1

    def _initial_test_suite(self, suite_result):
        test_suite_element = self.data_helper.initial_suite_element()
        test_suite_attributes = {
            ReportConstant.name: suite_result.suite_name,
            ReportConstant.time: round(float(suite_result.run_time) / 1000, 3),
            ReportConstant.errors: 0,
            ReportConstant.disabled: 0,
            ReportConstant.failures: 0,
            ReportConstant.ignored: 0,
            ReportConstant.tests: suite_result.test_num,
            ReportConstant.message: suite_result.stacktrace,
            ReportConstant.report: suite_result.report
        }
        if self.kwargs.get(ReportConstant.module_name, ""):
            test_suite_attributes[ReportConstant.module_name] = self.kwargs.get(
                ReportConstant.module_name, "")
        return test_suite_element, test_suite_attributes

    def _initial_test_case(self, case_result):
        test_case_element = self.data_helper.initial_case_element()
        case_stacktrace = str(case_result.stacktrace)
        for char_index in range(32):
            if char_index in [10, 13]:  # chr(10): LF, chr(13): CR
                continue
            case_stacktrace = case_stacktrace.replace(chr(char_index), "")
        test_case_attributes = {
            ReportConstant.name: case_result.test_name,
            ReportConstant.status: "",
            ReportConstant.time: round(float(case_result.run_time) / 1000, 3),
            ReportConstant.class_name: case_result.test_class,
            ReportConstant.result: "",
            ReportConstant.level: 1,
            ReportConstant.message: case_stacktrace,
            ReportConstant.report: case_result.report
        }
        result_content = getattr(case_result, ReportConstant.result_content, "")
        if result_content:
            formated_value = f"<![CDATA[{json.dumps(result_content, separators=(',', ':'))}]]>"
            test_case_attributes.update({ReportConstant.result_content: formated_value})
        start_time = getattr(case_result, ReportConstant.start_time, "")
        if start_time:
            test_case_attributes.update({ReportConstant.start_time: start_time})
        return test_case_element, test_case_attributes

    def _initial_test_element(self, test_result: dict):
        test_element = self.data_helper.initial_test_element()
        error = str(test_result.get("error", ""))
        for char_index in range(32):
            if char_index in [10, 13]:  # chr(10): LF, chr(13): CR
                continue
            error = error.replace(chr(char_index), "")
        test_attributes = {
            ReportConstant.name: test_result.get("name"),
            ReportConstant.time: str(test_result.get("time")),
            ReportConstant.result: "true" if test_result.get("result") == "Passed" else "false",
            ReportConstant.result_kind: test_result.get("result"),
            ReportConstant.message: error,
        }
        return test_element, test_attributes

    @classmethod
    def clear_report_result(cls):
        with SUITE_REPORTER_LOCK:
            LOG.debug("Clear report result")
            cls.suite_report_result.clear()

    @classmethod
    def clear_failed_case_list(cls):
        with SUITE_REPORTER_LOCK:
            LOG.debug("Clear failed case list")
            cls.failed_case_list.clear()

    @classmethod
    def append_report_result(cls, report_result):
        with SUITE_REPORTER_LOCK:
            if not isinstance(report_result, tuple) or len(report_result) != 2:
                LOG.error("Report result should be a tuple with length 2")
                return
            data_path = report_result[0]
            for index, exist_result in enumerate(cls.suite_report_result):
                if exist_result[0] == data_path:
                    LOG.debug("Data report %s generate again", data_path)
                    cls.suite_report_result[index] = report_result
                    return
            cls.suite_report_result.append(report_result)
            cls._upload_case_result(report_result[1])

    @classmethod
    def _upload_case_result(cls, result_str):
        if Context.session().mode != ModeType.decc:
            return
        element = DataHelper.parse_data_report(result_str)
        if len(element) == 0:
            LOG.debug("%s is error", result_str)
            return
        element = element[0]
        result, error_msg = Case.get_case_result(element)
        case_name = element.get(ReportConstant.name, "")
        try:
            from agent.decc import Handler
            LOG.info("Upload case result to decc")
            Handler.upload_case_result(case_name, result, error_msg)
        except ModuleNotFoundError as error:
            if Context.session().mode == ModeType.decc:
                LOG.error("Module not found %s", error.args)

    @classmethod
    def get_report_result(cls):
        with SUITE_REPORTER_LOCK:
            LOG.debug("Get report result, length is {}".
                      format(len(cls.suite_report_result)))
            return SuiteReporter.suite_report_result

    @classmethod
    def set_suite_list(cls, suite_list):
        LOG.debug("Set suite list, length is {}".format(len(suite_list)))
        cls.suite_list = suite_list

    @classmethod
    def get_suite_list(cls):
        with SUITE_REPORTER_LOCK:
            LOG.debug("Get suite list, length is {}".
                      format(len(cls.suite_list)))
            return SuiteReporter.suite_list

    @classmethod
    def get_failed_case_list(cls):
        with SUITE_REPORTER_LOCK:
            LOG.debug("Get failed case list, length is {}".
                      format(len(cls.failed_case_list)))
            return SuiteReporter.failed_case_list

    @classmethod
    def append_history_result(cls, suite_reports):
        from _core.utils import get_filename_extension
        with SUITE_REPORTER_LOCK:
            LOG.debug("Append history result,suite reports length is {}".
                      format(len(suite_reports)))
            for report_path, report_result in suite_reports:
                module_name = get_filename_extension(report_path)[0]
                cls.history_report_result. \
                    append((module_name, report_path, report_result))

    @classmethod
    def clear_history_result(cls):
        with SUITE_REPORTER_LOCK:
            LOG.debug("Clear history result")
            cls.history_report_result.clear()

    @classmethod
    def get_history_result_by_module(cls, name):
        with SUITE_REPORTER_LOCK:
            LOG.debug("Get history result by module,module_name:{}".
                      format(name))
            for module_name, report_path, report_result in \
                    cls.history_report_result:
                if name == module_name:
                    return report_path, report_result
            return "", ""

    @classmethod
    def get_history_result_list(cls):
        with SUITE_REPORTER_LOCK:
            LOG.debug("Get history result list,length is {}".
                      format(len(cls.history_report_result)))
            return cls.history_report_result
