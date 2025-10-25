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

import importlib
import importlib.abc
import importlib.machinery as _machinery
from typing import Dict, Any, List, Tuple, Optional, Callable
from .logger import logger
from .dynamic_hook import make_default_time_hook, register_dynamic_hook


class SymbolWatchFinder(importlib.abc.MetaPathFinder):
    """监听配置中的 symbol 模块导入，动态应用 hooks"""
    
    def __init__(self):
        self._symbol_hooks = {}
        self._config_loaded = False
        self._applied_hooks = set()  # 记录已应用的 hook，避免重复
    
    def load_symbol_config(self, config_data: List[Dict[str, Any]]):
        """加载 symbol 配置"""
        self._symbol_hooks = {}
        for i, symbol_config in enumerate(config_data):
            symbol_id = f"symbol_{i}"
            self._symbol_hooks[symbol_id] = symbol_config
        self._config_loaded = True
        logger.debug(f"Loaded {len(self._symbol_hooks)} symbol configurations")
    
    def find_spec(self, fullname, path, target=None):
        # 检查是否是配置中的 symbol 模块
        if not self._is_target_symbol(fullname):
            return None
            
        # 委托给标准 PathFinder
        spec = _machinery.PathFinder.find_spec(fullname, path)
        if spec is None or spec.loader is None:
            return spec

        # 避免重复包装
        if getattr(spec.loader, "_vllm_profiler_wrapped", False):
            return spec

        orig_loader = spec.loader

        class LoaderWrapper(importlib.abc.Loader):
            _vllm_profiler_wrapped = True

            def create_module(self, spec_):
                if hasattr(orig_loader, "create_module"):
                    return orig_loader.create_module(spec_)
                return None

            def exec_module(self, module):
                orig_loader.exec_module(module)
                # 调用外层类的方法
                self._finder._on_symbol_module_loaded(fullname)

        wrapper = LoaderWrapper()
        wrapper._finder = self
        spec.loader = wrapper
        return spec
    
    def _is_target_symbol(self, fullname):
        """检查是否是配置中的目标 symbol 模块"""
        if not self._config_loaded:
            return False
        
        # 检查是否匹配配置中的任何 symbol
        for symbol_info in self._symbol_hooks.values():
            symbol_path = symbol_info['symbol']
            # 提取模块路径（去掉类名和方法名）
            module_path = symbol_path.split(':')[0]
            if fullname == module_path:
                logger.debug(f"SymbolWatchFinder: Direct match for {fullname} -> {symbol_path}")
                return True
            # 同时监听父包导入事件：当父包被加载时，后续子模块导入仍会触发
            if module_path.startswith(fullname + "."):
                logger.debug(f"SymbolWatchFinder: Parent package match for {fullname} -> {symbol_path}")
                return True
        return False
    
    def _on_symbol_module_loaded(self, fullname: str):
        """当 symbol 模块加载完成时的回调"""
        logger.debug(f"SymbolWatchFinder: Module loaded callback for {fullname}")
        # 找到该模块对应的所有 symbols
        module_symbols = []
        for symbol_id, symbol_info in self._symbol_hooks.items():
            symbol_path = symbol_info['symbol']
            module_path = symbol_path.split(':')[0]
            if fullname == module_path:
                module_symbols.append((symbol_id, symbol_info))
            # 若当前加载的是父包，尝试安全导入子模块以触发后续事件
            elif module_path.startswith(fullname + "."):
                try:
                    importlib.import_module(module_path)
                except Exception as e:
                    logger.debug(f"Failed to import {module_path}: {e}")
        
        if module_symbols:
            logger.debug(f"Detected symbol module loaded: {fullname}, applying {len(module_symbols)} hooks")
            for symbol_id, symbol_info in module_symbols:
                logger.debug(f"  - Applying hook for {symbol_info['symbol']}")
            self._apply_symbol_hooks_for_module(fullname, module_symbols)
    
    def _apply_symbol_hooks_for_module(self, module_name: str, module_symbols: List[Tuple[str, Dict[str, Any]]]):
        """为特定模块应用 symbol hooks"""
        try:
            for symbol_id, symbol_info in module_symbols:
                self._apply_single_symbol_hook(symbol_id, symbol_info)
                
        except Exception as e:
            logger.error(f"Failed to apply symbol hooks for module {module_name}: {e}")
    
    def _parse_symbol_path(self, symbol_path: str) -> Tuple[str, str, Optional[str]]:
        """解析 symbol 路径，返回 (module_path, method_name, class_name)"""
        module_path, class_method = symbol_path.split(':')
        if '.' in class_method:
            class_name, method_name = class_method.split('.')
            return module_path, method_name, class_name
        else:
            return module_path, class_method, None

    def _create_handler_function(self, symbol_info: dict, method_name: str) -> Callable:
        """创建处理函数，支持自定义 handler 或默认 timer"""
        handler_path = symbol_info.get('handler')
        
        if not handler_path:
            logger.debug(f"No handler specified for symbol {symbol_info['symbol']}, using default timer")
            return make_default_time_hook(
                domain=symbol_info.get('domain', "Default"),
                name=symbol_info.get('name', method_name),
                attributes=symbol_info.get('attributes')
            )
        else:
            # 解析自定义 handler
            handler_module, handler_func = handler_path.split(':')
            handler_module_obj = importlib.import_module(handler_module)
            return getattr(handler_module_obj, handler_func)

    def _build_hook_points(self, module_path: str, method_name: str, class_name: Optional[str]) -> List[Tuple[str, str]]:
        """构建 hook 点列表"""
        hook_point = f"{class_name}.{method_name}" if class_name else method_name
        return [(module_path, hook_point)]

    def _register_and_apply_hook(self, symbol_info: dict, hook_points: List[Tuple[str, str]], handler_func_obj: Callable):
        """注册并应用 hook"""
        # 注册动态 hook
        hooker = register_dynamic_hook(
            hook_list=hook_points,
            hook_func=handler_func_obj,
            min_version=symbol_info.get('min_version'),
            max_version=symbol_info.get('max_version'),
            caller_filter=symbol_info.get('caller_filter')
        )
        
        # 立即应用 hook
        hooker.init()
        return hooker

    def _apply_single_symbol_hook(self, symbol_id: str, symbol_info: dict):
        """应用单个 symbol 的 hook"""
        try:
            symbol_path = symbol_info['symbol']
            
            # 检查是否已经应用过这个 hook
            if symbol_path in self._applied_hooks:
                logger.debug(f"Hook for {symbol_path} already applied, skipping")
                return
            
            # 解析 symbol 路径
            module_path, method_name, class_name = self._parse_symbol_path(symbol_path)
            
            # 创建处理函数
            handler_func_obj = self._create_handler_function(symbol_info, method_name)
            
            # 构建 hook 点列表
            hook_points = self._build_hook_points(module_path, method_name, class_name)
            
            # 注册并应用 hook
            self._register_and_apply_hook(symbol_info, hook_points, handler_func_obj)
            
            # 记录已应用的 hook
            self._applied_hooks.add(symbol_path)
            
            logger.debug(f"Applied hook for symbol {symbol_path}")
            
        except Exception as e:
            logger.error(f"Failed to apply hook for symbol {symbol_path}: {e}")
