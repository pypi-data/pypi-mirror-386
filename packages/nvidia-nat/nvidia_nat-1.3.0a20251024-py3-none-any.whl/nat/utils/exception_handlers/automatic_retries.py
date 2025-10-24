# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
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
import asyncio
import copy
import functools
import inspect
import logging
import re
import time
import types
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Sequence
from typing import Any
from typing import TypeVar

T = TypeVar("T")
Exc = tuple[type[BaseException], ...]  # exception classes
CodePattern = int | str | range  # for retry_codes argument
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
#  Helpers: status-code extraction & pattern matching
# ──────────────────────────────────────────────────────────────────────────────
_CODE_ATTRS = ("code", "status", "status_code", "http_status")


def _extract_status_code(exc: BaseException) -> int | None:
    """Return a numeric status code found inside *exc*, else None."""
    for attr in _CODE_ATTRS:
        if hasattr(exc, attr):
            try:
                return int(getattr(exc, attr))
            except (TypeError, ValueError):
                pass
    if exc.args:
        try:
            return int(exc.args[0])
        except (TypeError, ValueError):
            pass
    return None


def _pattern_to_regex(pat: str) -> re.Pattern[str]:
    """
    Convert simple wildcard pattern (“4xx”, “5*”, “40x”) to a ^regex$.
    Rule:  ‘x’ or ‘*’ ⇒ any digit.
    """
    escaped = re.escape(pat)
    return re.compile("^" + escaped.replace(r"\*", r"\d").replace("x", r"\d") + "$")


def _code_matches(code: int, pat: CodePattern) -> bool:
    if isinstance(pat, int):
        return code == pat
    if isinstance(pat, range):
        return code in pat
    return bool(_pattern_to_regex(pat).match(str(code)))


# ──────────────────────────────────────────────────────────────────────────────
#  Unified retry-decision helper
# ──────────────────────────────────────────────────────────────────────────────
def _want_retry(
    exc: BaseException,
    *,
    code_patterns: Sequence[CodePattern] | None,
    msg_substrings: Sequence[str] | None,
) -> bool:
    """
    Return True if the exception satisfies *either* (when provided):
       • code_patterns  – matches status-code pattern(s)
       • msg_substrings – contains any of the substrings (case-insensitive)
    """

    if not code_patterns and not msg_substrings:
        logger.info("Retrying on exception %s without extra filters", exc)
        return True

    # -------- status-code filter --------
    if code_patterns is not None:
        code = _extract_status_code(exc)
        if any(_code_matches(code, p) for p in code_patterns):
            logger.info("Retrying on exception %s with matched code %s", exc, code)
            return True

    # -------- message filter -----------
    if msg_substrings is not None:
        msg = str(exc).lower()
        if any(s.lower() in msg for s in msg_substrings):
            logger.info("Retrying on exception %s with matched message %s", exc, msg)
            return True

    return False


# ──────────────────────────────────────────────────────────────────────────────
#  Core decorator factory (sync / async / (a)gen)
# ──────────────────────────────────────────────────────────────────────────────
def _retry_decorator(
    *,
    retries: int = 3,
    base_delay: float = 0.25,
    backoff: float = 2.0,
    retry_on: Exc = (Exception, ),
    retry_codes: Sequence[CodePattern] | None = None,
    retry_on_messages: Sequence[str] | None = None,
    deepcopy: bool = False,
    instance_context_aware: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Build a decorator that retries with exponential back-off *iff*:

      • the raised exception is an instance of one of `retry_on`
      • AND `_want_retry()` returns True (i.e. matches codes/messages filters)

    If both `retry_codes` and `retry_on_messages` are None, all exceptions are retried.

    deepcopy:
        If True, each retry receives deep‑copied *args and **kwargs* to avoid
        mutating shared state between attempts.

    instance_context_aware:
        If True, the decorator will check for a retry context flag on the first
        argument (assumed to be 'self'). If the flag is set, retries are skipped
        to prevent retry storms in nested method calls.
    """

    def decorate(fn: Callable[..., T]) -> Callable[..., T]:
        use_deepcopy = deepcopy
        use_context_aware = instance_context_aware

        class _RetryContext:
            """Context manager for instance-level retry gating."""

            __slots__ = ("_obj", "_enabled", "_active")

            def __init__(self, args: tuple[Any, ...]):
                self._obj = args[0] if (use_context_aware and args) else None
                self._enabled = bool(self._obj)
                self._active = False

            def __enter__(self):
                if not self._enabled:
                    return False
                try:
                    # If already in retry context, signal caller to skip retries
                    if getattr(self._obj, "_in_retry_context", False):
                        return True
                    object.__setattr__(self._obj, "_in_retry_context", True)
                    self._active = True
                    return False
                except Exception:
                    # If we cannot set the attribute, behave as if context isn't enabled
                    self._enabled = False
                    return False

            def __exit__(self, _exc_type, _exc, _tb):
                if self._enabled and self._active:
                    try:
                        object.__setattr__(self._obj, "_in_retry_context", False)
                    except Exception:
                        pass

        async def _call_with_retry_async(*args, **kw) -> T:
            with _RetryContext(args) as already_in_context:
                if already_in_context:
                    return await fn(*args, **kw)
                delay = base_delay
                for attempt in range(retries):
                    call_args = copy.deepcopy(args) if use_deepcopy else args
                    call_kwargs = copy.deepcopy(kw) if use_deepcopy else kw
                    try:
                        return await fn(*call_args, **call_kwargs)
                    except retry_on as exc:
                        if (not _want_retry(exc, code_patterns=retry_codes, msg_substrings=retry_on_messages)
                                or attempt == retries - 1):
                            raise
                        await asyncio.sleep(delay)
                        delay *= backoff

        async def _agen_with_retry(*args, **kw):
            with _RetryContext(args) as already_in_context:
                if already_in_context:
                    async for item in fn(*args, **kw):
                        yield item
                    return
                delay = base_delay
                for attempt in range(retries):
                    call_args = copy.deepcopy(args) if use_deepcopy else args
                    call_kwargs = copy.deepcopy(kw) if use_deepcopy else kw
                    try:
                        async for item in fn(*call_args, **call_kwargs):
                            yield item
                        return
                    except retry_on as exc:
                        if (not _want_retry(exc, code_patterns=retry_codes, msg_substrings=retry_on_messages)
                                or attempt == retries - 1):
                            raise
                        await asyncio.sleep(delay)
                        delay *= backoff

        def _gen_with_retry(*args, **kw) -> Iterable[Any]:
            with _RetryContext(args) as already_in_context:
                if already_in_context:
                    yield from fn(*args, **kw)
                    return
                delay = base_delay
                for attempt in range(retries):
                    call_args = copy.deepcopy(args) if use_deepcopy else args
                    call_kwargs = copy.deepcopy(kw) if use_deepcopy else kw
                    try:
                        yield from fn(*call_args, **call_kwargs)
                        return
                    except retry_on as exc:
                        if (not _want_retry(exc, code_patterns=retry_codes, msg_substrings=retry_on_messages)
                                or attempt == retries - 1):
                            raise
                        time.sleep(delay)
                        delay *= backoff

        def _sync_with_retry(*args, **kw) -> T:
            with _RetryContext(args) as already_in_context:
                if already_in_context:
                    return fn(*args, **kw)
                delay = base_delay
                for attempt in range(retries):
                    call_args = copy.deepcopy(args) if use_deepcopy else args
                    call_kwargs = copy.deepcopy(kw) if use_deepcopy else kw
                    try:
                        return fn(*call_args, **call_kwargs)
                    except retry_on as exc:
                        if (not _want_retry(exc, code_patterns=retry_codes, msg_substrings=retry_on_messages)
                                or attempt == retries - 1):
                            raise
                        time.sleep(delay)
                        delay *= backoff

        # Decide which wrapper to return
        if inspect.iscoroutinefunction(fn):
            wrapper = _call_with_retry_async
        elif inspect.isasyncgenfunction(fn):
            wrapper = _agen_with_retry
        elif inspect.isgeneratorfunction(fn):
            wrapper = _gen_with_retry
        else:
            wrapper = _sync_with_retry

        return functools.wraps(fn)(wrapper)  # type: ignore[return-value]

    return decorate


# ──────────────────────────────────────────────────────────────────────────────
#  Public helper : patch_with_retry
# ──────────────────────────────────────────────────────────────────────────────
def patch_with_retry(
    obj: Any,
    *,
    retries: int = 3,
    base_delay: float = 0.25,
    backoff: float = 2.0,
    retry_on: Exc = (Exception, ),
    retry_codes: Sequence[CodePattern] | None = None,
    retry_on_messages: Sequence[str] | None = None,
    deepcopy: bool = False,
) -> Any:
    """
    Patch *obj* instance-locally so **every public method** retries on failure.

    Extra filters
    -------------
    retry_codes
        Same as before – ints, ranges, or wildcard strings (“4xx”, “5*”…).
    retry_on_messages
        List of *substring* patterns.  We retry only if **any** pattern
        appears (case-insensitive) in `str(exc)`.
    deepcopy:
        If True, each retry receives deep‑copied *args and **kwargs* to avoid
        mutating shared state between attempts.
    """
    deco = _retry_decorator(
        retries=retries,
        base_delay=base_delay,
        backoff=backoff,
        retry_on=retry_on,
        retry_codes=retry_codes,
        retry_on_messages=retry_on_messages,
        deepcopy=deepcopy,
        instance_context_aware=True,  # Prevent retry storms
    )

    # Choose attribute source: the *class* to avoid triggering __getattr__
    cls = obj if inspect.isclass(obj) else type(obj)
    cls_name = getattr(cls, "__name__", str(cls))

    for name, _ in inspect.getmembers(cls, callable):
        descriptor = inspect.getattr_static(cls, name)

        # Skip dunders, privates and all descriptors we must not wrap
        if (name.startswith("_") or isinstance(descriptor, property | staticmethod | classmethod)):
            continue

        original = descriptor.__func__ if isinstance(descriptor, types.MethodType) else descriptor
        wrapped = deco(original)

        try:  # instance‑level first
            if not inspect.isclass(obj):
                object.__setattr__(obj, name, types.MethodType(wrapped, obj))
                continue
        except Exception as exc:
            logger.info(
                "Instance‑level patch failed for %s.%s (%s); "
                "falling back to class‑level patch.",
                cls_name,
                name,
                exc,
            )

        try:  # class‑level fallback
            setattr(cls, name, wrapped)
        except Exception as exc:
            logger.info(
                "Cannot patch method %s.%s with automatic retries: %s",
                cls_name,
                name,
                exc,
            )

    return obj
