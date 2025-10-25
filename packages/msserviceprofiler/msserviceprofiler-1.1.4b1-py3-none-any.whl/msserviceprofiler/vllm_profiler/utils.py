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

import os
import importlib.metadata as importlib_metadata
from typing import Optional, Dict, Any, List
from .logger import logger


def find_config_path() -> Optional[str]:
    """Find profiling config file with priority:
    1) vllm_ascend installation directory: vllm_ascend/profiling_config/service_profiling_symbols.yaml
    2) This project: <this>/config/service_profiling_symbols.yaml
    """
    # 1) vllm_ascend installation path
    try:
        # Try common distribution/package names
        for dist_name in ('vllm-ascend', 'vllm_ascend'):
            try:
                dist = importlib_metadata.distribution(dist_name)  # type: ignore
            except Exception:
                continue
            # Resolve the package directory using locate_file on the package name
            try:
                ascend_pkg_dir = dist.locate_file('vllm_ascend')  # type: ignore
                ascend_dir = os.fspath(ascend_pkg_dir)
            except Exception:
                ascend_dir = None
            if ascend_dir and os.path.isdir(ascend_dir):
                candidate = os.path.join(ascend_dir, 'profiling_config', 'service_profiling_symbols.yaml')
                if os.path.isfile(candidate):
                    logger.debug(f"Using profiling symbols from vllm_ascend distribution: {candidate}")
                    return candidate
    except Exception:
        pass

    # 2) local project config path
    local_candidate = os.path.join(os.path.dirname(__file__), 'config', 'service_profiling_symbols.yaml')
    if os.path.isfile(local_candidate):
        logger.debug(f"Using profiling symbols from local project: {local_candidate}")
        return local_candidate

    return None


def load_yaml_config(config_path: str) -> Optional[List[Dict[str, Any]]]:
    """加载 YAML 配置文件"""
    try:
        import yaml
    except ImportError:
        logger.error("PyYAML is required for configuration loading")
        return None
        
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if isinstance(config, list):
                return config
            else:
                logger.warning("Configuration file should be a list of hook configurations")
                return []
    except FileNotFoundError:
        logger.warning(f"Configuration file does not exist: {config_path}")
        return None
    except Exception as e:
        logger.error(f"Failed to load YAML configuration: {e}")
        return None


def parse_version_tuple(version_str: str) -> tuple:
    """解析版本字符串为元组"""
    parts = version_str.split("+")[0].split("-")[0].split(".")
    nums = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            break
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3])


def auto_detect_v1_default() -> str:
    """Auto decide default V1 usage based on installed vLLM version.

    Heuristic: for newer vLLM (>= 0.9.2) default to V1, otherwise V0.
    If version can't be determined, fall back to V0 for safety.
    """
    try:
        vllm_version = importlib_metadata.version("vllm")
        major, minor, patch = parse_version_tuple(vllm_version)
        use_v1 = (major, minor, patch) >= (0, 9, 2)
        logger.info(
            f"VLLM_USE_V1 not set, auto-detected via vLLM {vllm_version}: default {'1' if use_v1 else '0'}"
        )
        return "1" if use_v1 else "0"
    except Exception as e:
        logger.info("VLLM_USE_V1 not set and vLLM version unknown; default to 0 (V0)")
        return "0"
