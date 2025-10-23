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

"""Mixed common stuff not big enough for a separate module"""

import asyncio
import hashlib
import logging
import os
import re
import shlex
import time
from collections.abc import (
    AsyncIterable,
    Awaitable,
    Callable,
    Coroutine,
    Iterable,
    Iterator,
    Mapping,
)
from concurrent.futures import Executor
from contextlib import contextmanager, suppress
from datetime import datetime
from functools import partial, reduce, wraps
from pathlib import Path
from subprocess import DEVNULL, check_output
from typing import (
    TYPE_CHECKING,
    NoReturn,
    ParamSpec,
    TypeVar,
    overload,
)

from dateutil import tz

ReturnT = TypeVar("ReturnT")
ArgumentsP = ParamSpec("ArgumentsP")


def log() -> logging.Logger:
    """Returns the logger instance to use here"""
    return logging.getLogger("trickkiste.misc")


def throw(exception: BaseException) -> NoReturn:
    """Function for throwing exceptions in order to become functional
    >>> try:
    ...     [1 / (x if x != 42 else throw(SystemExit)) for x in (23, 42, 401)]
    ... except SystemExit:
    ...     print("The question is '[retracted]'")
    The question is '[retracted]'
    """
    raise exception


def md5from(filepath: Path) -> None | str:
    """Returns an MD5 sum from contents of file provided"""
    with suppress(FileNotFoundError):
        with filepath.open("rb") as input_file:
            file_hash = hashlib.md5()  # noqa: S324 Probable use of insecure hash function
            while chunk := input_file.read(1 << 16):
                file_hash.update(chunk)
            return file_hash.hexdigest()
    return None


@contextmanager
def cwd(path: Path) -> Iterator[None]:
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def dur_str(seconds: float, fixed: bool = False) -> str:
    """Turns a duration defined by @seconds into a string like '1d:2h:3m'
    If @fixed is True, numbers will be 0-padded for uniform width.
    Negative values for @seconds are not supported (yet)
    >>> dur_str(42)
    '42s'
    >>> dur_str(12345)
    '3h:25m:45s'
    """
    if not fixed and not seconds:
        return "0s"
    digits = 2 if fixed else 1
    days = (
        f"{int(seconds // 86400):0{digits}d}d"
        if fixed or seconds >= 86400
        else ""
    )
    hours = (
        f"{int(seconds // 3600 % 24):0{digits}d}h"
        if fixed or (seconds >= 3600 and (seconds % 86400))
        else ""
    )
    minutes = (
        f"{int(seconds // 60 % 60):0{digits}d}m"
        if fixed or (seconds >= 60 and (seconds % 3600))
        else ""
    )
    seconds_str = (
        f"{int(seconds % 60):0{digits}d}s"
        if not fixed and ((seconds % 60) or seconds == 0)
        else ""
    )
    return ":".join(e for e in (days, hours, minutes, seconds_str) if e)


def age_str(
    now: float | datetime, age: None | int | datetime, fixed: bool = False
) -> str:
    """Turn a number of seconds into something human readable
    >>> age_str(1700000000, 1600000000)
    '1157d:9h:46m:40s'
    """
    if age is None:
        return "--"
    age_ts = age.timestamp() if isinstance(age, datetime) else age
    now_ts = now.timestamp() if isinstance(now, datetime) else now
    if (age_ts or now_ts) <= 0.0:
        return "--"
    return dur_str(now_ts - age_ts, fixed=fixed)


def date_str(
    timestamp: int | datetime, datefmt: str = "%Y.%m.%d-%H:%M:%S"
) -> str:
    """Returns a uniform time string from a timestamp or a datetime
    >>> date_str(datetime.strptime("1980.01.04-12:55:02", "%Y.%m.%d-%H:%M:%S"))
    '1980.01.04-12:55:02'
    >>> date_str(315834902)
    '1980.01.04-12:55:02'
    """
    if not timestamp:
        return "--"
    date_dt = (
        timestamp
        if isinstance(timestamp, datetime)
        else datetime.fromtimestamp(timestamp, tz=tz.tzlocal())
    )
    if date_dt.year < 1000:
        return "--"
    return (date_dt).strftime(datefmt)


def date_from(timestamp: float | str) -> None | datetime:
    """Convenience date parser for a couple of time representations
    >>> str(date_from("2023-07-14T15:05:32.174200714+02:00"))
    '2023-07-14 15:05:32+02:00'
    >>> str(date_from("2023-07-24T21:25:26.89389821+02:00"))
    '2023-07-24 21:25:26+02:00'
    >>> str(date_from(1758173336.9167209))
    '2025-09-18 07:28:56.916721+02:00'
    """
    try:
        if isinstance(timestamp, datetime):
            return timestamp

        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp, tz=tz.tzlocal())

        if timestamp[-1] == "Z":
            return (
                datetime.strptime(timestamp[:19], "%Y-%m-%dT%H:%M:%S")
                .replace(tzinfo=tz.tzutc())
                .astimezone(tz.tzlocal())
            )
        if re.match(
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+\+\d{2}:\d{2}$",
            timestamp,
        ):
            timestamp = timestamp[:19] + timestamp[-6:]
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")
    except OverflowError:
        return None
    except Exception as exc:  # pylint: disable=broad-except
        raise ValueError(
            f"Could not parse datetime from <{timestamp!r}> ({exc})"
        ) from exc


def parse_age(string: str) -> int:
    """Return seconds extracted from something parsable as an age ('3d:4h')
    >>> parse_age("3600")
    3600
    >>> parse_age("3h")
    10800
    >>> parse_age("1d:10h")
    122400
    >>> parse_age("1d10h")
    122400
    >>> parse_age("1.5d")
    129600
    """
    number = r"\d*(?:\.(?:\d*)?)?"
    with suppress(ValueError):
        return int(string)
    if match := re.match(
        (
            "(?i)^"
            f"(?:({number})d)?"
            "(?::)?"
            f"(?:({number})h)?"
            "(?::)?"
            f"(?:({number})m)?"
            "(?::)?"
            f"(?:({number})s)?$"
        ),
        string,
    ):
        days, hours, mins, secs = match.groups()
        return int(
            float(days or "0") * 86400
            + float(hours or "0") * 3600
            + float(mins or "0") * 60
            + float(secs or "0")
        )
    raise ValueError(f"Cannot turn {string!r} into duration")


def smart_split(string: str, delimiter: str = ",") -> Iterator[str]:
    r"""Like str.split but takes quotes and parenthesis into account
    >>> list(smart_split("(=,),'a=x',\"b=y\""))
    ['(=,)', "'a=x'", '"b=y"']
    """
    splits: list[int] = []
    closers: list[str] = []
    parenthizers = {'"': '"', "'": "'", "[": "]", "(": ")"}
    for i, char in enumerate(string):
        if char == delimiter and not closers:
            splits.append(i)
        elif closers and char == closers[-1]:
            closers.pop()
        elif char in parenthizers:
            closers.append(parenthizers[char])
    start = 0
    for pos in splits:
        yield string[start:pos]
        start = pos + 1
    yield string[start:]


def multi_replace(string: str, *substitutions: tuple[str, str]) -> str:
    """Returns @string with given list of @substituions applied using str.replace
    >>> multi_replace("Mama", ("ma", "mr"), ("a", "i"), ("M", "B"), ("m", "e"))
    'Bier'
    """
    return reduce(lambda s, r: s.replace(*r), substitutions, string)


def split_params(string: str) -> Mapping[str, str]:
    """Splits a 'string packed map' into a dict
    >>> split_params("foo=23,bar=42,true='pi=3,14'")
    {'foo': '23', 'bar': '42', 'true': "'pi=3,14'"}
    """
    return {
        k: v
        for p in smart_split(string, ",")
        if p
        for k, v in (p.split("=", 1),)
    }


def compact_dict(
    mapping: Mapping[str, float | str],
    *,
    maxlen: None | int = 10,
    delim: str = ", ",
) -> str:
    """Turns a dict into a 'string packed map' (for making a dict human readable)
    >>> compact_dict({'foo': '23', 'bar': '42'})
    'foo=23, bar=42'
    """

    def short(string: str) -> str:
        return (
            string
            if maxlen is None or len(string) <= maxlen
            else f"{string[: maxlen - 2]}.."
        )

    return delim.join(
        f"{k}={short_str}"
        for k, v in mapping.items()
        if (short_str := short(str(v)))
    )


def process_output(cmd: str) -> str:
    """Return command output as one blob
    >>> process_output("echo hello world").strip()
    'hello world'
    """
    return check_output(  # noqa: S603  # `subprocess` call: check for execution of untrusted input
        shlex.split(cmd),
        stderr=DEVNULL,
        text=True,
    )


def asyncify(
    func: Callable[ArgumentsP, ReturnT],
) -> Callable[ArgumentsP, Awaitable[ReturnT]]:
    """Turns a synchronous function into an asynchronous one"""

    @wraps(func)
    async def run(  # type: ignore[valid-type]
        *args: ArgumentsP.args,
        loop: None | asyncio.AbstractEventLoop = None,
        executor: None | Executor = None,
        **kwargs: ArgumentsP.kwargs,
    ) -> ReturnT:
        return await (loop or asyncio.get_event_loop()).run_in_executor(
            executor, partial(func, *args, **kwargs)
        )

    return run  # type: ignore[return-value]  # (no clue yet how to solve this)


if TYPE_CHECKING:

    @overload
    def awatch_duration(
        function: (Callable[ArgumentsP, Awaitable[ReturnT]]),
        *,
        warn_timeout: float = 1.0,
    ) -> Callable[ArgumentsP, Coroutine[None, None, ReturnT]]: ...

    @overload
    def awatch_duration(
        *,
        warn_timeout: float = 1.0,
    ) -> Callable[
        [Callable[ArgumentsP, Awaitable[ReturnT]]],
        Callable[ArgumentsP, Coroutine[None, None, ReturnT]],
    ]: ...


def awatch_duration(
    function: (Callable[ArgumentsP, Awaitable[ReturnT]] | None) = None,
    *,
    warn_timeout: float = 1.0,
) -> (
    Callable[
        [Callable[ArgumentsP, Awaitable[ReturnT]]],
        Callable[ArgumentsP, Coroutine[None, None, ReturnT]],
    ]
    | Callable[ArgumentsP, Coroutine[None, None, ReturnT]]
):
    """Decorator for async functions which must not take too long to finish"""

    def decorator(
        afunc: Callable[ArgumentsP, Awaitable[ReturnT]],
    ) -> Callable[ArgumentsP, Coroutine[None, None, ReturnT]]:
        @wraps(afunc)
        async def decorated(
            *args: ArgumentsP.args, **kwargs: ArgumentsP.kwargs
        ) -> ReturnT:
            time_start = time.time()
            result = await afunc(*args, **kwargs)
            duration = time.time() - time_start
            if duration > warn_timeout:
                log().warning("%s took %.2fms", afunc, duration * 1000)
            return result

        return decorated

    if function is None:
        return decorator
    return decorator(function)


_default_logger = logging.getLogger(__name__)


if TYPE_CHECKING:

    @overload
    def async_retry(
        function: Callable[ArgumentsP, Awaitable[ReturnT]],
        *,
        exceptions: type[BaseException] = Exception,
        tries: int = -1,
        delay: float = 0,
        logger: logging.Logger = _default_logger,
    ) -> Callable[ArgumentsP, Coroutine[None, None, ReturnT]]: ...

    @overload
    def async_retry(
        *,
        exceptions: type[BaseException] = Exception,
        tries: int = -1,
        delay: float = 0,
        logger: logging.Logger = _default_logger,
    ) -> Callable[
        [Callable[ArgumentsP, Awaitable[ReturnT]]],
        Callable[ArgumentsP, Coroutine[None, None, ReturnT]],
    ]: ...


def async_retry(
    function: Callable[ArgumentsP, Awaitable[ReturnT]] | None = None,
    *,
    exceptions: type[BaseException] = Exception,
    tries: int = -1,
    delay: float = 0,
    logger: logging.Logger = _default_logger,
) -> (
    Callable[
        [Callable[ArgumentsP, Awaitable[ReturnT]]],
        Callable[ArgumentsP, Coroutine[None, None, ReturnT]],
    ]
    | Callable[ArgumentsP, Coroutine[None, None, ReturnT]]
):
    """Decorator for async functions which have to be retried on error"""

    def decorator(
        afunc: Callable[ArgumentsP, Awaitable[ReturnT]],
    ) -> Callable[ArgumentsP, Coroutine[None, None, ReturnT]]:
        @wraps(afunc)
        async def decorated(
            *args: ArgumentsP.args, **kwargs: ArgumentsP.kwargs
        ) -> ReturnT:
            attempt = 0
            while True:
                attempt += 1
                try:
                    return await afunc(*args, **kwargs)
                except exceptions as exc:
                    if attempt == tries:
                        raise
                    if logger is not None:
                        logger.warning(
                            "%s raised an exception %d times now (this time: %r)."
                            " retrying in %s seconds...",
                            afunc,
                            attempt,
                            exc,
                            delay,
                        )
                    await asyncio.sleep(delay)
            raise RuntimeError("make ruff(RET503) and mypy (return) happy")

        return decorated

    if function is None:
        return decorator
    return decorator(function)


async def async_chain(
    iterator: AsyncIterable[Iterable[ReturnT]],
) -> AsyncIterable[ReturnT]:
    """Turns a nested async iterable into a flattened iterable"""
    async for elems in iterator:
        for elem in elems:
            yield elem


async def async_filter(
    filter_fn: Callable[[ReturnT], bool],
    iterator: AsyncIterable[Iterable[ReturnT]],
) -> AsyncIterable[Iterable[ReturnT]]:
    """Applies filter() to nested iterables"""
    async for elems in iterator:
        # don't return empty lists
        if result := list(filter(filter_fn, elems)):
            yield result
