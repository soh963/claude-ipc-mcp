#!/usr/bin/env python3
"""
Plugin Manager for Unified IPC System
Codex's implementation - Dynamic plugin loading and lifecycle management
"""

import os
import sys
import importlib
import importlib.util
import inspect
from typing import Dict, List, Optional, Any, Type
from pathlib import Path
from collections import OrderedDict
import logging

from .base import PluginBase, PluginInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing plugins"""

    def __init__(self):
        self.plugins: OrderedDict[str, PluginBase] = OrderedDict()
        self.hooks: Dict[str, List[callable]] = {}

    def register(self, plugin: PluginBase) -> bool:
        """Register a plugin"""
        info = plugin.get_info()

        if info.name in self.plugins:
            logger.warning(f"Plugin {info.name} already registered")
            return False

        self.plugins[info.name] = plugin
        logger.info(f"Registered plugin: {info.name} v{info.version}")
        return True

    def unregister(self, name: str) -> bool:
        """Unregister a plugin"""
        if name in self.plugins:
            del self.plugins[name]
            logger.info(f"Unregistered plugin: {name}")
            return True
        return False

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get a plugin by name"""
        return self.plugins.get(name)

    def list_plugins(self) -> List[str]:
        """List all registered plugins"""
        return list(self.plugins.keys())


class DependencyResolver:
    """Resolve plugin dependencies"""

    def __init__(self):
        self.dependency_graph: Dict[str, List[str]] = {}

    def add_plugin(self, plugin: PluginBase):
        """Add plugin to dependency graph"""
        info = plugin.get_info()
        self.dependency_graph[info.name] = info.dependencies or []

    def resolve_order(self) -> List[str]:
        """Resolve plugin loading order based on dependencies"""
        visited = set()
        order = []

        def visit(name: str):
            if name in visited:
                return

            visited.add(name)

            # Visit dependencies first
            for dep in self.dependency_graph.get(name, []):
                if dep in self.dependency_graph:
                    visit(dep)

            order.append(name)

        # Visit all plugins
        for plugin_name in self.dependency_graph:
            visit(plugin_name)

        return order

    def check_circular(self) -> bool:
        """Check for circular dependencies"""
        visited = set()
        rec_stack = set()

        def has_cycle(name: str) -> bool:
            visited.add(name)
            rec_stack.add(name)

            for dep in self.dependency_graph.get(name, []):
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(name)
            return False

        for plugin_name in self.dependency_graph:
            if plugin_name not in visited:
                if has_cycle(plugin_name):
                    return True

        return False


class PluginLoader:
    """Load plugins dynamically"""

    def __init__(self, plugin_dir: Path = None):
        self.plugin_dir = plugin_dir or Path.home() / '.claude-ipc-data' / 'plugins'
        self.plugin_dir.mkdir(parents=True, exist_ok=True)

    def load_plugin_from_file(self, file_path: Path) -> Optional[PluginBase]:
        """Load a plugin from a Python file"""
        try:
            # Load module spec
            spec = importlib.util.spec_from_file_location(
                file_path.stem,
                file_path
            )

            if not spec or not spec.loader:
                logger.error(f"Failed to load spec for {file_path}")
                return None

            # Load module
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Find plugin class
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                logger.error(f"No plugin class found in {file_path}")
                return None

            # Create instance
            plugin = plugin_class()
            return plugin

        except Exception as e:
            logger.error(f"Failed to load plugin from {file_path}: {e}")
            return None

    def _find_plugin_class(self, module) -> Optional[Type[PluginBase]]:
        """Find plugin class in module"""
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and
                issubclass(obj, PluginBase) and
                obj != PluginBase):
                return obj
        return None

    def discover_plugins(self) -> List[Path]:
        """Discover plugin files in plugin directory"""
        plugin_files = []

        # Search for Python files
        for file in self.plugin_dir.glob('*.py'):
            if not file.name.startswith('_'):
                plugin_files.append(file)

        # Search in subdirectories
        for dir in self.plugin_dir.iterdir():
            if dir.is_dir() and not dir.name.startswith('_'):
                init_file = dir / '__init__.py'
                if init_file.exists():
                    plugin_files.append(init_file)

        return plugin_files


class PluginManager:
    """Main plugin manager with all functionality"""

    def __init__(self, plugin_dir: Path = None):
        self.registry = PluginRegistry()
        self.resolver = DependencyResolver()
        self.loader = PluginLoader(plugin_dir)

        # Plugin lifecycle hooks
        self.hooks = {
            'pre_load': [],
            'post_load': [],
            'pre_unload': [],
            'post_unload': []
        }

        logger.info("Plugin Manager initialized")

    def load_all(self):
        """Load all plugins from plugin directory"""
        plugin_files = self.loader.discover_plugins()
        logger.info(f"Discovered {len(plugin_files)} plugin files")

        plugins = []

        # Load each plugin
        for file in plugin_files:
            plugin = self.loader.load_plugin_from_file(file)
            if plugin:
                plugins.append(plugin)
                self.resolver.add_plugin(plugin)

        # Check for circular dependencies
        if self.resolver.check_circular():
            logger.error("Circular dependencies detected")
            return

        # Resolve loading order
        load_order = self.resolver.resolve_order()

        # Register and initialize in order
        for plugin_name in load_order:
            plugin = next((p for p in plugins if p.get_info().name == plugin_name), None)
            if plugin:
                self._load_plugin(plugin)

    def _load_plugin(self, plugin: PluginBase) -> bool:
        """Load and initialize a single plugin"""
        info = plugin.get_info()

        # Run pre-load hooks
        for hook in self.hooks['pre_load']:
            hook(plugin)

        # Validate dependencies
        if not plugin.validate_dependencies():
            logger.error(f"Plugin {info.name} has unmet dependencies")
            return False

        # Register plugin
        if not self.registry.register(plugin):
            return False

        # Initialize plugin
        try:
            if plugin.initialize():
                plugin.initialized = True
                plugin.on_enable()
                logger.info(f"Plugin {info.name} loaded successfully")

                # Run post-load hooks
                for hook in self.hooks['post_load']:
                    hook(plugin)

                return True
            else:
                logger.error(f"Plugin {info.name} initialization failed")
                self.registry.unregister(info.name)
                return False

        except Exception as e:
            logger.error(f"Plugin {info.name} initialization error: {e}")
            self.registry.unregister(info.name)
            return False

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin"""
        plugin = self.registry.get_plugin(name)
        if not plugin:
            return False

        # Run pre-unload hooks
        for hook in self.hooks['pre_unload']:
            hook(plugin)

        # Disable and shutdown
        plugin.on_disable()

        try:
            plugin.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down plugin {name}: {e}")

        # Unregister
        self.registry.unregister(name)

        # Run post-unload hooks
        for hook in self.hooks['post_unload']:
            hook(plugin)

        logger.info(f"Plugin {name} unloaded")
        return True

    def reload_plugin(self, name: str) -> bool:
        """Reload a plugin"""
        plugin = self.registry.get_plugin(name)
        if not plugin:
            return False

        # Store config
        config = plugin.config

        # Unload
        self.unload_plugin(name)

        # Find and reload
        plugin_files = self.loader.discover_plugins()
        for file in plugin_files:
            new_plugin = self.loader.load_plugin_from_file(file)
            if new_plugin and new_plugin.get_info().name == name:
                new_plugin.config = config
                return self._load_plugin(new_plugin)

        return False

    def handle_message(self, message: Dict) -> Optional[Dict]:
        """Pass message through all plugins"""
        for name, plugin in self.registry.plugins.items():
            if plugin.enabled and plugin.initialized:
                try:
                    result = plugin.handle_message(message)
                    if result:
                        # Plugin handled the message
                        return result
                except Exception as e:
                    logger.error(f"Plugin {name} error handling message: {e}")

        return None

    def register_hook(self, event: str, callback: callable):
        """Register a lifecycle hook"""
        if event in self.hooks:
            self.hooks[event].append(callback)

    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """Get plugin information"""
        plugin = self.registry.get_plugin(name)
        return plugin.get_info() if plugin else None

    def list_plugins(self) -> Dict[str, Dict]:
        """List all plugins with their status"""
        plugins = {}

        for name, plugin in self.registry.plugins.items():
            info = plugin.get_info()
            plugins[name] = {
                'version': info.version,
                'author': info.author,
                'description': info.description,
                'enabled': plugin.enabled,
                'initialized': plugin.initialized
            }

        return plugins


# Example plugin implementation
class ExamplePlugin(PluginBase):
    """Example plugin implementation"""

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name='example',
            version='1.0.0',
            author='Codex',
            description='Example plugin for testing'
        )

    def initialize(self) -> bool:
        logger.info("Example plugin initializing...")
        return True

    def shutdown(self) -> bool:
        logger.info("Example plugin shutting down...")
        return True

    def handle_message(self, message: Dict) -> Optional[Dict]:
        if message.get('type') == 'example':
            return {'status': 'handled', 'plugin': 'example'}
        return None


def main():
    """Test plugin manager"""
    manager = PluginManager()

    # Create example plugin
    plugin = ExamplePlugin()

    # Load plugin
    manager._load_plugin(plugin)

    # List plugins
    plugins = manager.list_plugins()
    print(f"Loaded plugins: {plugins}")

    # Test message handling
    result = manager.handle_message({'type': 'example'})
    print(f"Message result: {result}")

    # Unload plugin
    manager.unload_plugin('example')


if __name__ == "__main__":
    main()