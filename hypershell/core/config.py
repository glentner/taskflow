# SPDX-FileCopyrightText: 2021 Geoffrey Lentner
# SPDX-License-Identifier: Apache-2.0

"""Runtime configuration for HyperShell."""


# standard libs
import os
import ctypes
import logging

# external libs
from cmdkit.config import Namespace, Configuration

# public interface
__all__ = ['default', 'config', 'get_site', 'init_paths', 'load', 'update', ]


# environment variables and configuration files are automatically
# depth-first merged with defaults
default = Namespace({
    'database': {
        'provider': 'sqlite',
    },
    'logging': {
        'level': 'warning',
        'format': '%(ansi_color)s%(levelname)-7s%(ansi_reset)s [%(name)s] %(msg)s',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    },
    'submit': {
        'bundlesize': 1,
        'bundlewait': 5  # Seconds
    },
    'server': {
        'bind': 'localhost',
        'port': 50_001,
        'auth': '__HYPERSHELL__BAD__AUTHKEY__',
        'queuesize': 2,
        'bundlesize': 1,
        'attempts': 1,
        'eager': False,  # prefer failed tasks to new tasks
        'wait': 5  # Seconds to wait between database queries
    },
    'client': {
        'bundlesize': 1,
        'bundlewait': 5  # Seconds
    }
})


cwd = os.getcwd()
home = os.getenv('HOME')
if os.name == 'nt':
    is_admin = ctypes.windll.shell32.IsUserAnAdmin() == 1
    site = Namespace(system=os.path.join(os.getenv('ProgramData'), 'HyperShell'),
                     user=os.path.join(os.getenv('AppData'), 'HyperShell'),
                     local=cwd)
    path = Namespace({
        'system': {
            'lib': os.path.join(site.system, 'Library'),
            'config': os.path.join(site.system, 'Config.toml'),
            'log': os.path.join(site.system, 'Logs')},
        'user': {
            'lib': os.path.join(site.user, 'Library'),
            'config': os.path.join(site.user, 'Config.toml'),
            'log': os.path.join(site.user, 'Logs')},
        'local': {
            'lib': os.path.join(site.local, 'lib'),
            'config': os.path.join(site.local, 'config.toml'),
            'log': os.path.join(site.local, 'log')},
    })
else:
    is_admin = os.getuid() == 0
    site = Namespace(system='/', user=os.path.join(home, '.hypershell'),
                     local=os.path.join(cwd, '.hypershell'))
    path = Namespace({
        'system': {
            'lib': os.path.join(site.system, 'var', 'lib', 'hypershell'),
            'config': os.path.join(site.system, 'etc', 'hypershell.toml'),
            'log': os.path.join(site.system, 'var', 'log', 'hypershell')},
        'user': {
            'lib': os.path.join(site.user, 'lib'),
            'config': os.path.join(site.user, 'config.toml'),
            'log': os.path.join(site.user, 'log')},
        'local': {
            'lib': os.path.join(site.local, 'lib'),
            'config': os.path.join(site.local, 'config.toml'),
            'log': os.path.join(site.local, 'log')},
    })


def get_site() -> Namespace:
    """Retrieve path namespace for either 'system' (if admin) or 'user'."""
    return path.system if is_admin else path.user


def init_paths() -> None:
    """Automatically create necessary directories."""
    os.makedirs(get_site().get('lib'), exist_ok=True)
    os.makedirs(get_site().get('log'), exist_ok=True)


def load() -> Configuration:
    """Load configuration."""
    return Configuration.from_local(env=True, prefix='HYPERSHELL', default=DEFAULT,
                                    system=path.system.config, user=path.user.config, local=path.local.config)


# global configuration instance is set on import (but can be reloaded)
config: Configuration = load()


def update(scope: str, data: dict) -> None:
    """
    Extend the current configuration and commit it to disk.

    Args:
        scope (str):
            Either "local", "user", or "system"
        data (dict):
            Sectioned mappable to update configuration file.

    Example:
        >>> update('user', {
        ...    'logging': {
        ...        'level': 'debug'
        ...    }
        ... })
    """
    config_path = path[scope].config
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    new_config = Namespace.from_local(config_path)
    new_config.update(data)
    new_config.to_local(config_path)
