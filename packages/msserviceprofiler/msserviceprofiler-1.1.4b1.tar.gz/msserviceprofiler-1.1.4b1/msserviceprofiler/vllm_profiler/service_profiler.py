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
import sys
from .logger import logger
from .utils import find_config_path, load_yaml_config, auto_detect_v1_default
from .symbol_watcher import SymbolWatchFinder


class ServiceProfiler:
    """服务分析器主类"""
    
    def __init__(self):
        self._hooks_applied = False
        self._symbol_watcher = None
        self._vllm_use_v1 = self._detect_vllm_version()
    
    def _detect_vllm_version(self) -> str:
        """检测 vLLM 版本"""
        env_v1 = os.environ.get('VLLM_USE_V1')
        return env_v1 if env_v1 is not None else auto_detect_v1_default()
    
    def initialize(self):
        """初始化服务分析器"""
        # 检查是否启用了打点
        if not os.environ.get('SERVICE_PROF_CONFIG_PATH'):
            logger.debug("SERVICE_PROF_CONFIG_PATH not set, skipping hooks")
            return
            
        logger.debug("Initializing service profiler")
        
        # 加载配置文件
        config_data = self._load_config()
        if not config_data:
            logger.warning("No configuration loaded, skipping profiler initialization")
            return
        
        # 按版本导入内置 hookers
        self._import_hookers()
        
        # 初始化 symbol 监听器
        self._init_symbol_watcher(config_data)
        
        # 应用传统 hooks（回退机制）
        self._apply_traditional_hooks()
        
        self._hooks_applied = True
        logger.debug("Service profiler initialized successfully")
    
    def _load_config(self):
        """加载配置文件"""
        cfg_path = find_config_path()
        if not cfg_path:
            logger.warning("No config file found")
            return None
            
        return load_yaml_config(cfg_path)
    
    def _import_hookers(self):
        """按版本导入内置 hookers"""
        if self._vllm_use_v1 == "0":
            logger.debug("Initializing service profiler with vLLM V0 interface")
            from .vllm_v0 import batch_hookers, kvcache_hookers, model_hookers, request_hookers  # noqa: F401
        elif self._vllm_use_v1 == "1":
            logger.debug("Initializing service profiler with vLLM V1 interface")
            from .vllm_v1 import batch_hookers, kvcache_hookers, meta_hookers, model_hookers, request_hookers  # noqa: F401
        else:
            logger.error(f"unknown vLLM interface version: VLLM_USE_V1={self._vllm_use_v1}")
            return
    
    def _init_symbol_watcher(self, config_data):
        """初始化 symbol 监听器"""
        self._symbol_watcher = SymbolWatchFinder()
        self._symbol_watcher.load_symbol_config(config_data)
        
        # 安装到 sys.meta_path
        sys.meta_path.insert(0, self._symbol_watcher)
        logger.debug("Symbol watcher installed")
        
        # 检查目标模块是否已经被导入，如果是则立即应用 hooks
        self._check_and_apply_existing_modules()
    
    def _apply_traditional_hooks(self):
        """应用传统 hooks（回退机制）"""
        # 完全跳过传统 hooks 应用，只使用 SymbolWatchFinder 进行动态加载
        logger.debug("Skipping traditional hooks application, using SymbolWatchFinder for dynamic loading")
        # 不再调用 apply_hooks()，避免重复应用
    
    def _check_and_apply_existing_modules(self):
        """检查目标模块是否已经被导入，如果是则立即应用 hooks"""
        
        logger.debug("Checking for already loaded modules...")
        for _, symbol_info in self._symbol_watcher._symbol_hooks.items():
            symbol_path = symbol_info['symbol']
            module_path = symbol_path.split(':')[0]
            
            logger.debug(f"Checking module {module_path} for symbol {symbol_path}")
            logger.debug(f"  - Module in sys.modules: {module_path in sys.modules}")
            logger.debug(f"  - Symbol already applied: {symbol_path in self._symbol_watcher._applied_hooks}")
            
            # 检查模块是否已导入，且该 symbol 尚未应用
            if module_path in sys.modules and symbol_path not in self._symbol_watcher._applied_hooks:
                logger.debug(f"Module {module_path} already loaded, applying hooks immediately")
                # 模拟模块加载完成事件
                self._symbol_watcher._on_symbol_module_loaded(module_path)
