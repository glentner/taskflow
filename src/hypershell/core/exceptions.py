# SPDX-FileCopyrightText: 2022 Geoffrey Lentner
# SPDX-License-Identifier: Apache-2.0

"""Core exception handling useful for import-time issues."""


# type annotations
from typing import Union, Callable

# standard libraries
import os
import sys
import logging
import functools
import traceback
from datetime import datetime

# external libs
from cmdkit.app import exit_status
from cmdkit.config import Namespace

# internal libs
from hypershell.core.ansi import faint, bold, magenta, yellow, red
from hypershell.core.platform import default_path

# public interface
__all__ = ['display_warning', 'display_error', 'display_critical', 'traceback_filepath', 'write_traceback',
           'handle_exception', 'handle_disconnect', 'handle_address_unknown', 'HostAddressInfo', ]


def _display_message(levelname: str, error: Union[Exception, str],
                     module: str = None, colorized: Callable[[str], str] = None) -> None:
    """Generic message display for import-time warnings and errors."""
    text = error if isinstance(error, str) else f'{error.__class__.__name__}: {error}'
    name = '' if not module else faint(f'[{module}]')
    level = levelname if colorized is None else bold(colorized(levelname))
    print(f'{level} {name} {text}', file=sys.stderr)


# Specialized methods for each severity level
display_warning = functools.partial(_display_message, 'WARNING', colorized=yellow)
display_error = functools.partial(_display_message, 'ERROR', colorized=red)
display_critical = functools.partial(_display_message, 'CRITICAL', colorized=magenta)


def traceback_filepath(path: Namespace = None) -> str:
    """Construct filepath for writing traceback."""
    path = path or default_path
    time = datetime.now().strftime('%Y%m%d-%H%M%S')
    return os.path.join(path.log, f'exception-{time}.log')


def write_traceback(exc: Exception, site: Namespace = None, logger: logging.Logger = None,
                    status: int = exit_status.uncaught_exception, module: str = None) -> int:
    """Write exception to file and return exit code."""
    write = functools.partial(display_critical, module=module) if not logger else logger.critical
    path = traceback_filepath(site)
    with open(path, mode='w') as stream:
        print(traceback.format_exc(), file=stream)
    write(f'{exc.__class__.__name__}: ' + str(exc).replace('\n', ' - '))
    write(f'Exception traceback written to {path}')
    return status


def handle_disconnect(exc: Exception, logger: logging.Logger) -> int:
    """An EOFError results from the server hanging up the client."""
    logger.critical(f'{exc.__class__.__name__}: server disconnected')
    return exit_status.runtime_error


def handle_exception(exc: Exception, logger: logging.Logger, status: int) -> int:
    """Log the exception argument and exit with `status`."""
    logger.critical(f'{exc.__class__.__name__}: ' + str(exc).replace('\n', ' - '))
    return status


class HostAddressInfo(Exception):
    """Could not resolve hostname."""


def handle_address_unknown(exc: Exception,  # noqa: unused
                           logger: logging.Logger,
                           status: int = exit_status.runtime_error) -> int:
    """Could not get address info for hostname (see `socket.gaierror`)."""
    logger.critical(f'{exc.__class__.__name__}: {exc}')
    return status
