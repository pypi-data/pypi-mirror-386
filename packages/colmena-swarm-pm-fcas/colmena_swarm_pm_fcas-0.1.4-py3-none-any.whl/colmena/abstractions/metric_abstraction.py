#!/usr/bin/env python3
#
#  Copyright 2002-2025 Barcelona Supercomputing Center (www.bsc.es)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

# -*- coding: utf-8 -*-

from typing import Callable
from colmena.logger import Logger


class MetricInterface:
    def __init__(self, name):
        self._name = name
        self.__publish_method = None
        self.__logger = Logger(self).get_logger()

    def _set_publish_method(self, func: Callable):
        self.__publish_method = func

    def publish(self, value: float):
        self.__publish_method(key=self._name, value=value)
