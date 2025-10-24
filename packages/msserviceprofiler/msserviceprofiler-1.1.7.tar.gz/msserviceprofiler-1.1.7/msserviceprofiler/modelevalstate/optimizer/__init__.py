# -*- coding: utf-8 -*-
# Copyright (c) 2025-2025 Huawei Technologies Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from msserviceprofiler.modelevalstate.optimizer.plugins.benchmark import VllmBenchMark
from msserviceprofiler.modelevalstate.optimizer.plugins.simulate import VllmSimulator
from msserviceprofiler.modelevalstate.optimizer.register import register_simulator, register_benchmarks

register_benchmarks("vllm_benchmark", VllmBenchMark)
register_simulator("vllm", VllmSimulator)