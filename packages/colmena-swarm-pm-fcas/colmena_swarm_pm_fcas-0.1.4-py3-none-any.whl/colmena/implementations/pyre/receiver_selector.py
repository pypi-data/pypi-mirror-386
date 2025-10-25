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
import logging
import random
import uuid

import numpy as np

from colmena.logger import Logger


def explore(current_peers):
    return random.choice(current_peers)


class LeastLatencySelector:
    def __init__(self, epsilon=0.1, alpha=0.9):
        self._logger = Logger(self).get_logger()
        self.epsilon = epsilon
        self.alpha = alpha
        self.latency_estimates = {}  # estimated latency for each recipient

    # e-greedy selection
    def select_recipient(self, current_peers: [uuid.UUID]):
        if len(self.latency_estimates) == 0 or random.random() < self.epsilon:
            return explore(current_peers)
        else:
            lowest_latency_recipient = uuid.UUID(self.exploit())
            if lowest_latency_recipient in current_peers:
                return lowest_latency_recipient
            else:
                return explore(current_peers)

    def exploit(self):
        values = np.array(list(self.latency_estimates.values()))
        min_index = np.argmin(values)
        return list(self.latency_estimates.keys())[min_index]

    def update_estimate(self, recipient_id: str, latency: float):
        if recipient_id not in self.latency_estimates:
            # init with first observed latency
            self.latency_estimates[recipient_id] = latency
        else:
            # Update the latency estimate w/ exponential moving average
            ema = self.alpha * latency + (1 - self.alpha) * self.latency_estimates[recipient_id]
            self.latency_estimates[recipient_id] = ema

        self._logger.debug(
            f"updated latency. recipient_id: {recipient_id}, latency: {latency}, "
            f"new estimate: {self.latency_estimates[recipient_id]}"
        )
