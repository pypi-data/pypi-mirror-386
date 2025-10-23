#!/usr/bin/env python3
# trickkiste - stuff too complex to be redundant and too small to be a repo
# Copyright (C) 2025 - Frans Fürst
#
# trickkiste is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# trickkiste is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details at
#  <http://www.gnu.org/licenses/>.
#
# Anyway this project is not free for commercial machine learning. If you're
# using any content of this repository to train any sort of machine learned
# model (e.g. LLMs), you agree to make the whole model trained with this
# repository and all data needed to train (i.e. reproduce) the model publicly
# and freely available (i.e. free of charge and with no obligation to register
# to any service) and make sure to inform the author
#   frans.fuerst@protonmail.com via email how to get and use that model and any
# sources needed to train it.

"""Common stuff shared among modules"""

import logging
import logging.handlers
import os
import sys
import threading
import traceback
from argparse import ArgumentParser
from collections.abc import Iterable
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.markup import escape as markup_escape

LOG_LEVELS = ("ALL_DEBUG", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL")
SHORT_COLOR_LEVEL_NAMES = {
    "NOTSET": "[dim]NN[/]",
    "DEBUG": "[green]DD[/]",
    "INFO": "[blue]II[/]",
    "WARNING": "[yellow]WW[/]",
    "ERROR": "[red bold]EE[/]",
    "CRITICAL": "[red bold reverse]CC[/]",
}
LogLevelSpec = int | str | tuple[str | logging.Logger, int | str]


def apply_common_logging_cli_args(parser: ArgumentParser) -> ArgumentParser:
    """Decorates given @parser with arguments for logging"""
    parser.add_argument(
        "--log-level",
        "-l",
        choices=LOG_LEVELS,
        help="Sets the logging level - ALL_DEBUG sets all other loggers to DEBUG, too",
        type=str.upper,
        default="INFO",
    )
    parser.add_argument(
        "--log-file",
        help="Write log output to given file",
        type=Path,
    )
    return parser


def stack_str(depth: int = 0) -> str:
    """Returns a short local function call stack"""

    def stack_fns() -> Iterable[str]:
        stack = list(
            reversed(
                traceback.extract_stack(sys._getframe(depth))  # noqa: SLF001 # Private member accessed
            )
        )

        for site in stack:
            if site.filename != stack[0].filename or site.name == "<module>":
                break
            yield site.name

    return ">".join(reversed(list(stack_fns())))


def markup_escape_filter(record: logging.LogRecord) -> bool:
    """Escapes log record contents in order to avoid unintended formatting"""
    record.args = record.args and tuple(
        markup_escape(arg) if isinstance(arg, str) else arg
        for arg in record.args
    )
    record.msg = markup_escape(record.msg)
    return True


def thread_id_filter(record: logging.LogRecord) -> bool:
    """Inject thread_id in log records"""
    record.posixTID = threading.get_native_id()
    return True


def callstack_filter(record: logging.LogRecord) -> bool:
    """Inject short function call stack in log records"""
    record.callstack = stack_str(5)
    return True


def logger_name_filter(record: logging.LogRecord) -> bool:
    """Inject thread_id to log records"""
    record.name = record.name.removeprefix("trickkiste.")
    return True


def logger_funcname_filter(
    record: logging.LogRecord, width: int, with_line_number: bool
) -> bool:
    """Inject augmented funcName with line number and link to source"""
    text = (
        f"{record.funcName}():{record.lineno}"
        if with_line_number
        else f"{record.funcName}()"
    )
    record.funcName = f"[link=file://{record.pathname}#{record.lineno}]{text}[/]{' ' * (width - len(text))}"
    return True


def logger_levelname_filter(record: logging.LogRecord) -> bool:
    """Shorten the level name (but keep the coloring)"""
    # we cannot use levelname because it get's handled by the RichHandler
    # another approach would be to register styles for
    # logging.level.<SHORTNAME> and set
    # record.levelname = <SHORTNAME>
    record.shortlevelname = SHORT_COLOR_LEVEL_NAMES[record.levelname]
    return True


def setup_logging(  # pylint: disable=too-many-arguments
    logger: logging.Logger | str,
    *,
    level: str | int = "INFO",
    show_level: bool = True,
    show_time: bool = True,
    show_name: bool | int = True,
    show_callstack: bool | int = False,
    show_funcname: bool | int = True,
    show_tid: bool | int = False,
    show_linenumber: bool = False,
    file_path: Path | None = None,
) -> None:
    """Make logging fun"""
    if not logging.getLogger().hasHandlers():
        setup_logging_handler(
            RichHandler(
                show_level=False,
                show_time=False,
                omit_repeated_times=True,
                show_path=False,
                markup=True,
                console=Console(
                    # rich defaults to stdout even for logging so we have to fix it here
                    stderr=True,
                    # also rich only runs isatty() on the output file to check whether to
                    # activate color, which can be True for sys.stderr in pipes.
                    # so we turn it off here if we know sys.stdout is not atty.
                    # In case FORCE_COLOR is set we leave it up to rich again (because otherwise
                    # we'd efectively ignore FORCE_COLOR when running in a pipe)
                    color_system=(
                        "auto"
                        if sys.stdout.isatty() or os.getenv("FORCE_COLOR")
                        else None
                    ),
                ),
            ),
            show_level,
            show_time,
            show_name,
            show_callstack,
            show_funcname,
            show_tid,
            show_linenumber,
            file_path,
        )

    set_log_levels((logger, level))

    logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)


def setup_logging_handler(
    handler: logging.Handler,
    show_level: bool,
    show_time: bool,
    show_name: bool | int,
    show_callstack: bool | int,
    show_funcname: bool | int,
    show_tid: bool | int,
    show_linenumber: bool,
    file_path: Path | None = None,
) -> None:
    """Handler setup, common among console and TUI"""

    def bool_to_int(val: int | bool, default: int) -> int:
        if not val:
            return 0
        if val is True:
            return default
        return val

    width_name = bool_to_int(show_name, 16)
    width_callstack = bool_to_int(show_callstack, 32)
    width_funcname = bool_to_int(show_funcname, 20)
    width_tid = bool_to_int(show_tid, 8)
    logging.getLogger().addHandler(handler)
    if show_callstack:
        handler.addFilter(callstack_filter)
    if show_funcname:
        handler.addFilter(
            lambda r: logger_funcname_filter(r, width_funcname, show_linenumber)
        )
    if show_tid:
        handler.addFilter(thread_id_filter)
    handler.addFilter(markup_escape_filter)
    handler.addFilter(logger_name_filter)
    handler.addFilter(logger_levelname_filter)

    handler.setFormatter(
        logging.Formatter(
            " │ ".join(
                str(elem)
                for elem in (
                    show_level and "%(shortlevelname)s",
                    show_time and "%(asctime)s",
                    width_tid and f"[grey53]%(posixTID)-{width_tid}s[/]",
                    width_name and f"[grey53]%(name)-{width_name}s[/]",
                    width_funcname and "[grey53]%(funcName)s[/]",
                    width_callstack
                    and f"[grey53]%(callstack)-{width_callstack}s[/]",
                    "[bold white]%(message)s[/]",
                )
                if elem
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    if file_path:
        logging.getLogger().addHandler(
            filehandler := logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=1_000_000,
                backupCount=1,
            )
        )
        filehandler.setFormatter(
            logging.Formatter("%(asctime)-15s::%(levelname)s::%(message)s")
        )


def set_log_levels(
    *levels: LogLevelSpec, others_level: int | str = logging.WARNING
) -> None:
    """Sets the overall log level for internal log console"""

    def level_of(level: str | int) -> int:
        """Returns numeral representation of provided level"""
        return (
            int(logging.getLevelName(level.split("_")[-1]))
            if isinstance(level, str)
            else level
        )

    match levels:
        case (level_spec,) if isinstance(level_spec, (str, int)):
            levels_spec = {"trickkiste": level_spec}
        case ((_logger, _level_spec), *_rest):
            assert isinstance(levels, tuple)
            levels_spec = {
                s[0] if isinstance(s[0], str) else s[0].name: s[1]
                for s in levels
                if isinstance(s, tuple)
            }
        case (others, (_logger, _level_spec), *_rest) if isinstance(
            others, (str, int)
        ):
            others_level = others
            levels_spec = {
                s[0] if isinstance(s[0], str) else s[0].name: s[1]
                for s in levels
                if isinstance(s, tuple)
            }
        case _:
            raise TypeError(f"unsupported arguments: {levels}")

    named_levels: dict[str | None, int] = {
        None: (
            logging.DEBUG
            if "ALL_DEBUG" in levels_spec.values()
            else level_of(others_level)
        ),
        "trickkiste": logging.DEBUG
        if "ALL_DEBUG" in levels_spec.values()
        else logging.INFO,
        **{
            logger_name: level_of(level_spec)
            for logger_name, level_spec in levels_spec.items()
        },
    }

    for handler in logging.getLogger().handlers:
        handler.setLevel(min(named_levels.values()))

    for name, level in named_levels.items():
        logging.getLogger(name).setLevel(level)
