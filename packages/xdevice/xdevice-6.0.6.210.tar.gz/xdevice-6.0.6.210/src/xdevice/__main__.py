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
from xdevice import Console
from xdevice import platform_logger
from xdevice import VERSION
from xdevice import TrackEvent, Tracker

srcpath = os.path.dirname(os.path.dirname(__file__))
sys.path.append(srcpath)

LOG = platform_logger("Main")


def main_process(command=None):
    LOG.info(
        "*************** xDevice Test Framework %s Starting ***************" %
        VERSION)
    if command:
        args = str(command).split(" ")
        args.insert(0, "xDevice")
    else:
        args = sys.argv
    event = TrackEvent.TestTask
    Tracker.event(event.value, event_name=event.name)
    console = Console()
    console.console(args)


if __name__ == "__main__":
    main_process()
